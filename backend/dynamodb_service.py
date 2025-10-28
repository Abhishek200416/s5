"""
DynamoDB Service Layer
Provides MongoDB-like interface for DynamoDB operations
"""
import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
import os
import logging
from typing import List, Dict, Any, Optional
from decimal import Decimal
import json

logger = logging.getLogger(__name__)


class DynamoDBService:
    """
    DynamoDB service that mimics MongoDB's interface for seamless migration
    """
    
    def __init__(self, region: str = 'us-east-1', table_prefix: str = 'AlertWhisperer_'):
        """
        Initialize DynamoDB service
        
        Args:
            region: AWS region (default: us-east-1)
            table_prefix: Prefix for all table names (default: AlertWhisperer)
        """
        self.region = region
        self.table_prefix = table_prefix
        
        # Initialize boto3 client (will use AWS credentials from environment or IAM role)
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        logger.info(f"DynamoDB service initialized for region: {region}")
        
    def _get_table(self, collection_name: str):
        """Get DynamoDB table by collection name"""
        # Convert collection name to table name (companies -> AlertWhisperer_Companies)
        # Capitalize first letter of each word (users -> Users, companyconfigs -> CompanyConfigs)
        words = collection_name.split('_')
        formatted_name = ''.join(word.capitalize() for word in words)
        table_name = f"{self.table_prefix}{formatted_name}"
        return self.dynamodb.Table(table_name)
    
    def _convert_to_json_serializable(self, item: Any) -> Any:
        """Convert DynamoDB Decimal types to JSON serializable types"""
        if isinstance(item, list):
            return [self._convert_to_json_serializable(i) for i in item]
        elif isinstance(item, dict):
            return {k: self._convert_to_json_serializable(v) for k, v in item.items()}
        elif isinstance(item, Decimal):
            if item % 1 == 0:
                return int(item)
            else:
                return float(item)
        else:
            return item
    
    
    def _convert_floats_to_decimal(self, item: Any) -> Any:
        """Convert float types to Decimal for DynamoDB compatibility"""
        if isinstance(item, list):
            return [self._convert_floats_to_decimal(i) for i in item]
        elif isinstance(item, dict):
            return {k: self._convert_floats_to_decimal(v) for k, v in item.items()}
        elif isinstance(item, float):
            return Decimal(str(item))
        else:
            return item

    def _apply_projection(self, item: Dict[str, Any], projection: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Apply MongoDB-style projection to a document
        
        Args:
            item: Document to apply projection to
            projection: MongoDB-style projection (e.g., {'_id': 0, 'password_hash': 0})
                       - {"field": 0} means exclude field
                       - {"field": 1} means include only these fields
        
        Returns:
            Projected document
        """
        if not projection or not item:
            return item
        
        # Handle exclusion projection ({"_id": 0, "password_hash": 0})
        has_exclusions = any(v == 0 for v in projection.values())
        has_inclusions = any(v == 1 for v in projection.values())
        
        if has_exclusions:
            # Exclude specified fields
            result = item.copy()
            for field, value in projection.items():
                if value == 0 and field in result:
                    del result[field]
            return result
        elif has_inclusions:
            # Include only specified fields
            result = {}
            for field, value in projection.items():
                if value == 1 and field in item:
                    result[field] = item[field]
            return result
        
        return item
    
    async def find_one(self, collection: str, query: Dict[str, Any], projection: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        Find a single document in a collection
        
        Args:
            collection: Collection name (e.g., 'users', 'companies')
            query: Query filter (e.g., {'id': '123'} or {'email': 'test@test.com'})
            projection: MongoDB-style projection (e.g., {'_id': 0, 'password_hash': 0})
            
        Returns:
            Document if found, None otherwise
        """
        table = self._get_table(collection)
        
        try:
            # If querying by id (primary key), use get_item
            if 'id' in query and len(query) == 1:
                response = table.get_item(Key={'id': query['id']})
                item = response.get('Item')
                if item:
                    item = self._convert_to_json_serializable(item)
                    return self._apply_projection(item, projection)
                return None
            
            # Otherwise, use scan with filter (handle pagination)
            filter_expression = None
            for key, value in query.items():
                # Handle MongoDB operators
                if isinstance(value, dict):
                    # Handle $in operator
                    if '$in' in value:
                        condition = Attr(key).is_in(value['$in'])
                    # Handle $ne operator
                    elif '$ne' in value:
                        condition = Attr(key).ne(value['$ne'])
                    # Handle $gt operator
                    elif '$gt' in value:
                        condition = Attr(key).gt(value['$gt'])
                    # Handle $gte operator
                    elif '$gte' in value:
                        condition = Attr(key).gte(value['$gte'])
                    # Handle $lt operator
                    elif '$lt' in value:
                        condition = Attr(key).lt(value['$lt'])
                    # Handle $lte operator
                    elif '$lte' in value:
                        condition = Attr(key).lte(value['$lte'])
                    else:
                        # Default to equality if no recognized operator
                        condition = Attr(key).eq(value)
                else:
                    # Simple equality check
                    condition = Attr(key).eq(value)
                filter_expression = condition if filter_expression is None else filter_expression & condition
            
            # Scan with pagination until we find a match
            scan_kwargs = {'FilterExpression': filter_expression}
            
            while True:
                response = table.scan(**scan_kwargs)
                items = response.get('Items', [])
                
                if items:
                    item = self._convert_to_json_serializable(items[0])
                    return self._apply_projection(item, projection)
                
                # Check if there are more items to scan
                if 'LastEvaluatedKey' not in response:
                    break
                
                # Continue scanning from last evaluated key
                scan_kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']
            
            return None
            
        except ClientError as e:
            logger.error(f"Error finding document in {collection}: {e}")
            return None
    
    async def find(self, collection: str, query: Dict[str, Any] = None, projection: Dict[str, Any] = None, limit: int = None) -> List[Dict[str, Any]]:
        """
        Find multiple documents in a collection
        
        Args:
            collection: Collection name
            query: Query filter (optional, if None returns all)
            projection: MongoDB-style projection (e.g., {'_id': 0})
            limit: Maximum number of results
            
        Returns:
            List of documents
        """
        table = self._get_table(collection)
        
        try:
            scan_kwargs = {}
            
            # Add filter expression if query provided
            if query:
                filter_expression = None
                for key, value in query.items():
                    # Handle MongoDB operators
                    if isinstance(value, dict):
                        # Handle $in operator
                        if '$in' in value:
                            condition = Attr(key).is_in(value['$in'])
                        # Handle $ne operator
                        elif '$ne' in value:
                            condition = Attr(key).ne(value['$ne'])
                        # Handle $gt operator
                        elif '$gt' in value:
                            condition = Attr(key).gt(value['$gt'])
                        # Handle $gte operator
                        elif '$gte' in value:
                            condition = Attr(key).gte(value['$gte'])
                        # Handle $lt operator
                        elif '$lt' in value:
                            condition = Attr(key).lt(value['$lt'])
                        # Handle $lte operator
                        elif '$lte' in value:
                            condition = Attr(key).lte(value['$lte'])
                        else:
                            # Default to equality if no recognized operator
                            condition = Attr(key).eq(value)
                    else:
                        # Simple equality check
                        condition = Attr(key).eq(value)
                    
                    filter_expression = condition if filter_expression is None else filter_expression & condition
                scan_kwargs['FilterExpression'] = filter_expression
            
            # Add limit if specified
            if limit:
                scan_kwargs['Limit'] = limit
            
            # Scan table
            response = table.scan(**scan_kwargs)
            items = response.get('Items', [])
            
            # Handle pagination if needed (without limit)
            while 'LastEvaluatedKey' in response and not limit:
                scan_kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']
                response = table.scan(**scan_kwargs)
                items.extend(response.get('Items', []))
            
            # Convert and apply projection
            result = []
            for item in items:
                converted = self._convert_to_json_serializable(item)
                projected = self._apply_projection(converted, projection)
                result.append(projected)
            
            return result
            
        except ClientError as e:
            logger.error(f"Error finding documents in {collection}: {e}")
            return []
    
    async def insert_one(self, collection: str, document: Dict[str, Any]) -> str:
        """
        Insert a single document
        
        Args:
            collection: Collection name
            document: Document to insert (must have 'id' field)
            
        Returns:
            Document ID
        """
        table = self._get_table(collection)
        
        try:
            # Ensure document has an id
            if 'id' not in document:
                raise ValueError("Document must have an 'id' field")
            
            # Convert floats to Decimal
            document = self._convert_floats_to_decimal(document)
            
            table.put_item(Item=document)
            logger.info(f"Inserted document {document['id']} into {collection}")
            return document['id']
            
        except ClientError as e:
            logger.error(f"Error inserting document into {collection}: {e}")
            raise
    
    async def update_one(self, collection: str, query: Dict[str, Any], update: Dict[str, Any], upsert: bool = False) -> bool:
        """
        Update a single document
        
        Args:
            collection: Collection name
            query: Query to find document (e.g., {'id': '123'})
            update: Update operations (e.g., {'$set': {'name': 'New Name'}})
            upsert: If True, insert document if it doesn't exist
            
        Returns:
            True if updated, False otherwise
        """
        table = self._get_table(collection)
        
        try:
            # Find the document first
            doc = await self.find_one(collection, query)
            
            if not doc:
                if upsert:
                    # Create new document with query fields and update fields
                    new_doc = {**query}
                    if '$set' in update:
                        new_doc.update(update['$set'])
                    
                    # Ensure 'id' field exists (required for DynamoDB)
                    if 'id' not in new_doc:
                        import uuid
                        new_doc['id'] = str(uuid.uuid4())
                    
                    # Convert floats to Decimal
                    new_doc = self._convert_floats_to_decimal(new_doc)
                    
                    table.put_item(Item=new_doc)
                    logger.info(f"Upserted new document in {collection} with query {query}")
                    return True
                else:
                    return False
            
            # Apply updates
            if '$set' in update:
                doc.update(update['$set'])
            
            # Convert floats to Decimal
            doc = self._convert_floats_to_decimal(doc)
            
            # Put updated document
            table.put_item(Item=doc)
            logger.info(f"Updated document in {collection} with query {query}")
            return True
            
        except ClientError as e:
            logger.error(f"Error updating document in {collection}: {e}")
            raise
    
    async def update_many(self, collection: str, query: Dict[str, Any], update: Dict[str, Any]) -> int:
        """
        Update multiple documents
        
        Args:
            collection: Collection name
            query: Query to find documents
            update: Update operations (e.g., {'$set': {'status': 'acknowledged'}})
            
        Returns:
            Number of documents updated
        """
        table = self._get_table(collection)
        
        try:
            # Find all matching documents
            docs = await self.find(collection, query)
            
            if not docs:
                return 0
            
            updated_count = 0
            for doc in docs:
                # Apply updates
                if '$set' in update:
                    doc.update(update['$set'])
                
                # Convert floats to Decimal
                doc = self._convert_floats_to_decimal(doc)
                
                # Put updated document
                table.put_item(Item=doc)
                updated_count += 1
            
            logger.info(f"Updated {updated_count} documents in {collection} with query {query}")
            return updated_count
            
        except ClientError as e:
            logger.error(f"Error updating documents in {collection}: {e}")
            return 0
            return False
    
    async def delete_one(self, collection: str, query: Dict[str, Any]) -> bool:
        """
        Delete a single document
        
        Args:
            collection: Collection name
            query: Query to find document (must include 'id')
            
        Returns:
            True if deleted, False otherwise
        """
        table = self._get_table(collection)
        
        try:
            # Must have id for delete
            if 'id' not in query:
                doc = await self.find_one(collection, query)
                if not doc:
                    return False
                query = {'id': doc['id']}
            
            table.delete_item(Key={'id': query['id']})
            logger.info(f"Deleted document from {collection} with query {query}")
            return True
            
        except ClientError as e:
            logger.error(f"Error deleting document from {collection}: {e}")
            return False
    
    async def count_documents(self, collection: str, query: Dict[str, Any] = None) -> int:
        """
        Count documents in a collection
        
        Args:
            collection: Collection name
            query: Query filter (optional)
            
        Returns:
            Number of documents
        """
        # For DynamoDB, we need to scan to count (expensive for large tables)
        items = await self.find(collection, query)
        return len(items)
    
    async def delete_many(self, collection: str, query: Dict[str, Any]) -> int:
        """
        Delete multiple documents
        
        Args:
            collection: Collection name
            query: Query filter
            
        Returns:
            Number of documents deleted
        """
        table = self._get_table(collection)
        
        try:
            # Find all matching documents
            items = await self.find(collection, query)
            
            # Delete each one
            deleted_count = 0
            for item in items:
                try:
                    table.delete_item(Key={'id': item['id']})
                    deleted_count += 1
                except ClientError as e:
                    logger.error(f"Error deleting item {item['id']}: {e}")
            
            logger.info(f"Deleted {deleted_count} documents from {collection}")
            return deleted_count
            
        except ClientError as e:
            logger.error(f"Error in delete_many for {collection}: {e}")
            return 0


# Create a MongoDB-like database interface
class DynamoDBDatabase:
    """
    Database interface that mimics MongoDB's database object
    Provides collection access via db[collection_name] or db.collection_name
    """
    
    def __init__(self, service: DynamoDBService):
        self.service = service
        self._collections = {}
    
    def __getitem__(self, collection_name: str):
        """Access collection via db['collection_name']"""
        if collection_name not in self._collections:
            self._collections[collection_name] = DynamoDBCollection(self.service, collection_name)
        return self._collections[collection_name]
    
    def __getattr__(self, collection_name: str):
        """Access collection via db.collection_name"""
        return self[collection_name]


class DynamoDBCollection:
    """
    Collection interface that mimics MongoDB's collection object
    """
    
    def __init__(self, service: DynamoDBService, collection_name: str):
        self.service = service
        self.name = collection_name
    
    async def find_one(self, query: Dict[str, Any] = None, projection: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Find a single document with optional projection"""
        return await self.service.find_one(self.name, query or {}, projection)
    
    def find(self, query: Dict[str, Any] = None, projection: Dict[str, Any] = None) -> 'DynamoDBCursor':
        """Find multiple documents - returns a cursor with optional projection"""
        return DynamoDBCursor(self.service, self.name, query or {}, projection)
    
    async def insert_one(self, document: Dict[str, Any]) -> Any:
        """Insert a single document"""
        doc_id = await self.service.insert_one(self.name, document)
        
        # Return MongoDB-like InsertOneResult
        class InsertOneResult:
            def __init__(self, inserted_id):
                self.inserted_id = inserted_id
        
        return InsertOneResult(doc_id)
    
    async def update_one(self, query: Dict[str, Any], update: Dict[str, Any], upsert: bool = False) -> Any:
        """Update a single document"""
        success = await self.service.update_one(self.name, query, update, upsert)
        
        # Return MongoDB-like UpdateResult
        class UpdateResult:
            def __init__(self, matched_count, modified_count):
                self.matched_count = matched_count
                self.modified_count = modified_count
        
        return UpdateResult(1 if success else 0, 1 if success else 0)
    
    
    async def update_many(self, query: Dict[str, Any], update: Dict[str, Any]) -> Any:
        """Update multiple documents"""
        count = await self.service.update_many(self.name, query, update)
        
        # Return MongoDB-like UpdateResult
        class UpdateResult:
            def __init__(self, matched_count, modified_count):
                self.matched_count = matched_count
                self.modified_count = modified_count
        
        return UpdateResult(count, count)

    async def delete_one(self, query: Dict[str, Any]) -> Any:
        """Delete a single document"""
        success = await self.service.delete_one(self.name, query)
        
        # Return MongoDB-like DeleteResult
        class DeleteResult:
            def __init__(self, deleted_count):
                self.deleted_count = deleted_count
        
        return DeleteResult(1 if success else 0)
    
    async def delete_many(self, query: Dict[str, Any]) -> Any:
        """Delete multiple documents"""
        count = await self.service.delete_many(self.name, query)
        
        # Return MongoDB-like DeleteResult
        class DeleteResult:
            def __init__(self, deleted_count):
                self.deleted_count = deleted_count
        
        return DeleteResult(count)
    
    async def count_documents(self, query: Dict[str, Any] = None) -> int:
        """Count documents"""
        return await self.service.count_documents(self.name, query or {})
    
    def aggregate(self, pipeline: List[Dict[str, Any]]) -> 'DynamoDBCursor':
        """
        Aggregate documents using MongoDB-style pipeline
        Note: This is a simplified implementation - DynamoDB doesn't support aggregation pipelines natively
        We'll simulate basic aggregation operations in memory
        """
        return DynamoDBAggregateCursor(self.service, self.name, pipeline)


class DynamoDBAggregateCursor:
    """
    Aggregate cursor for MongoDB-style aggregation pipeline
    Simplified implementation that processes aggregation in memory
    """
    
    def __init__(self, service: DynamoDBService, collection_name: str, pipeline: List[Dict[str, Any]]):
        self.service = service
        self.collection_name = collection_name
        self.pipeline = pipeline
    
    async def to_list(self, length: int = None) -> List[Dict[str, Any]]:
        """Execute aggregation pipeline and return results"""
        # Get all documents from collection
        items = await self.service.find(self.collection_name, {}, None, limit=None)
        
        # Process each stage of the pipeline
        for stage in self.pipeline:
            if "$match" in stage:
                # Filter documents
                match_query = stage["$match"]
                items = [item for item in items if self._matches(item, match_query)]
            
            elif "$group" in stage:
                # Group documents
                group_spec = stage["$group"]
                grouped = {}
                group_id = group_spec.get("_id")
                
                for item in items:
                    # Get the group key value
                    if isinstance(group_id, str) and group_id.startswith("$"):
                        key = item.get(group_id[1:])
                    else:
                        key = group_id
                    
                    if key not in grouped:
                        grouped[key] = {
                            "_id": key
                        }
                        # Initialize accumulators
                        for field, accumulator in group_spec.items():
                            if field != "_id":
                                if "$sum" in accumulator:
                                    grouped[key][field] = 0
                                elif "$count" in accumulator:
                                    grouped[key][field] = 0
                    
                    # Apply accumulators
                    for field, accumulator in group_spec.items():
                        if field != "_id":
                            if "$sum" in accumulator:
                                if accumulator["$sum"] == 1:
                                    grouped[key][field] += 1
                                else:
                                    grouped[key][field] += item.get(accumulator["$sum"][1:], 0)
                            elif "$count" in accumulator:
                                grouped[key][field] += 1
                
                items = list(grouped.values())
            
            elif "$sort" in stage:
                # Sort documents
                sort_spec = stage["$sort"]
                for field, direction in sorted(sort_spec.items(), reverse=True):
                    items.sort(key=lambda x: x.get(field, ''), reverse=(direction == -1))
            
            elif "$limit" in stage:
                # Limit results
                items = items[:stage["$limit"]]
            
            elif "$skip" in stage:
                # Skip documents
                items = items[stage["$skip"]:]
        
        # Apply length limit if specified
        if length:
            items = items[:length]
        
        return items
    
    def _matches(self, item: Dict[str, Any], query: Dict[str, Any]) -> bool:
        """Check if item matches query"""
        for key, value in query.items():
            if key == "$gt":
                continue  # Handle in parent
            
            if isinstance(value, dict):
                if "$gt" in value:
                    if item.get(key, 0) <= value["$gt"]:
                        return False
                elif "$gte" in value:
                    if item.get(key, 0) < value["$gte"]:
                        return False
                elif "$lt" in value:
                    if item.get(key, 0) >= value["$lt"]:
                        return False
                elif "$lte" in value:
                    if item.get(key, 0) > value["$lte"]:
                        return False
            else:
                if item.get(key) != value:
                    return False
        return True


class DynamoDBCursor:
    """
    Cursor interface that mimics MongoDB's cursor object
    """
    
    def __init__(self, service: DynamoDBService, collection_name: str, query: Dict[str, Any], projection: Dict[str, Any] = None):
        self.service = service
        self.collection_name = collection_name
        self.query = query
        self.projection = projection
        self._limit = None
        self._skip = None
        self._sort = None
    
    def limit(self, limit: int):
        """Set limit for query"""
        self._limit = limit
        return self
    
    def skip(self, skip: int):
        """Set skip for query"""
        self._skip = skip
        return self
    
    def sort(self, key: str, direction: int = 1):
        """Set sort for query"""
        self._sort = (key, direction)
        return self
    
    async def to_list(self, length: int = None) -> List[Dict[str, Any]]:
        """Convert cursor to list"""
        items = await self.service.find(self.collection_name, self.query, self.projection, limit=self._limit)
        
        # Apply skip if specified
        if self._skip:
            items = items[self._skip:]
        
        # Apply sort if specified
        if self._sort:
            key, direction = self._sort
            items.sort(key=lambda x: x.get(key, ''), reverse=(direction == -1))
        
        # Apply length limit if specified
        if length:
            items = items[:length]
        
        return items
    
    def __aiter__(self):
        """Make cursor async iterable"""
        self._items = None
        self._index = 0
        return self
    
    async def __anext__(self):
        """Async iteration"""
        if self._items is None:
            self._items = await self.to_list()
        
        if self._index >= len(self._items):
            raise StopAsyncIteration
        
        item = self._items[self._index]
        self._index += 1
        return item
