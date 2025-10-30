import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../App';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  Shield, LogOut, AlertTriangle, TrendingDown, Clock, CheckCircle, 
  Play, XCircle, ArrowRight, Activity, Database, Zap, FileText, User, Settings, Bell, Server, ArrowLeft, BookOpen
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import RealTimeDashboard from '../components/RealTimeDashboard';
import HowItWorksGuide from '../components/HowItWorksGuide';
import MSPWorkflowGuide from '../components/MSPWorkflowGuide';
import AlertCorrelation from '../components/AlertCorrelation';
import IncidentList from '../components/IncidentList';
import IncidentAnalysis from '../components/IncidentAnalysis';
import DecisionEngine from '../components/DecisionEngine';
import KPIDashboard from '../components/KPIDashboard';
import KPIImpactDashboard from '../components/KPIImpactDashboard';
import LiveKPIProof from '../components/LiveKPIProof';
import RealTimeActivityFeed from '../components/RealTimeActivityFeed';
import CompanyManagement from '../components/CompanyManagement';
import ActivityFeed from '../components/ActivityFeed';
import AssetInventory from '../components/AssetInventory';
import CustomRunbookManager from './CustomRunbookManager';
import DemoModeModal from '../components/DemoModeModal';

const Dashboard = ({ user, onLogout }) => {
  const navigate = useNavigate();
  const [companies, setCompanies] = useState([]);
  const [selectedCompany, setSelectedCompany] = useState(null);
  const [kpis, setKpis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [unreadCount, setUnreadCount] = useState(0);
  const [notifications, setNotifications] = useState([]);
  const [showNotifications, setShowNotifications] = useState(false);
  const [showMSPGuide, setShowMSPGuide] = useState(false);
  const [showDemoModal, setShowDemoModal] = useState(false);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const howItWorksRef = React.useRef(null);

  const scrollToHowItWorks = () => {
    howItWorksRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  useEffect(() => {
    loadCompanies();
    loadUnreadCount();
    setupWebSocket();
    
    // Poll for unread notifications every 30 seconds
    const interval = setInterval(loadUnreadCount, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (selectedCompany) {
      loadKPIs();
    }
  }, [selectedCompany]);

  const setupWebSocket = () => {
    const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
    const wsUrl = backendUrl.replace('http', 'ws').replace('/api', '') + '/ws';
    
    const ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
      console.log('Dashboard WebSocket connected');
    };
    
    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        console.log('Dashboard received WebSocket message:', message.type);
        
        // Trigger refresh for relevant message types
        if (
          message.type === 'alert_received' ||
          message.type === 'incident_created' ||
          message.type === 'incident_updated' ||
          message.type === 'notification' ||
          message.type === 'demo_progress'
        ) {
          // Increment refresh trigger to cause child components to reload
          setRefreshTrigger(prev => prev + 1);
          
          // Reload KPIs for dashboard updates
          if (selectedCompany) {
            loadKPIs();
          }
        }
        
        // Handle notification updates
        if (message.type === 'notification') {
          loadUnreadCount();
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };
    
    ws.onerror = (error) => {
      console.error('Dashboard WebSocket error:', error);
    };
    
    ws.onclose = () => {
      console.log('Dashboard WebSocket disconnected, reconnecting in 3s...');
      setTimeout(setupWebSocket, 3000);
    };
  };

  const loadUnreadCount = async () => {
    try {
      const response = await api.get('/notifications/unread-count');
      setUnreadCount(response.data.count);
    } catch (error) {
      console.error('Failed to load unread count:', error);
    }
  };

  const loadNotifications = async () => {
    try {
      const response = await api.get('/notifications?limit=10');
      setNotifications(response.data);
    } catch (error) {
      console.error('Failed to load notifications:', error);
    }
  };

  const markAsRead = async (notificationId) => {
    try {
      await api.put(`/notifications/${notificationId}/read`);
      await loadNotifications();
      await loadUnreadCount();
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
    }
  };

  const markAllAsRead = async () => {
    try {
      await api.put('/notifications/mark-all-read');
      await loadNotifications();
      await loadUnreadCount();
    } catch (error) {
      console.error('Failed to mark all as read:', error);
    }
  };

  const loadCompanies = async () => {
    try {
      const response = await api.get('/companies');
      setCompanies(response.data);
      
      // Try to restore from localStorage first
      const savedCompanyId = localStorage.getItem('selectedCompany');
      
      // Auto-select company based on saved preference or user access
      if (response.data.length > 0) {
        const userCompanyIds = user.company_ids || [];
        const userCompanies = response.data.filter(c => 
          userCompanyIds.includes(c.id)
        );
        
        // If there's a saved company and it's accessible, use it
        if (savedCompanyId && response.data.find(c => c.id === savedCompanyId)) {
          setSelectedCompany(savedCompanyId);
        }
        // Otherwise, auto-select first accessible company
        else if (userCompanies.length > 0) {
          setSelectedCompany(userCompanies[0].id);
          localStorage.setItem('selectedCompany', userCompanies[0].id);
        } else if (response.data.length > 0) {
          // If user has no specific companies, select first available
          setSelectedCompany(response.data[0].id);
          localStorage.setItem('selectedCompany', response.data[0].id);
        }
      }
    } catch (error) {
      console.error('Failed to load companies:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadKPIs = async () => {
    try {
      const response = await api.get(`/kpis/${selectedCompany}`);
      setKpis(response.data);
    } catch (error) {
      console.error('Failed to load KPIs:', error);
    }
  };

  const handleDemoCompanySelected = async (demoCompany) => {
    // Reload companies to include demo company
    await loadCompanies();
    // Select demo company
    setSelectedCompany(demoCompany.id);
  };

  const userCompanyIds = user.company_ids || [];
  // Admin users can see all companies, other users only see their assigned companies
  const userCompanies = user.role === 'admin' || user.role === 'msp_admin' 
    ? companies 
    : companies.filter(c => userCompanyIds.includes(c.id));
  const currentCompany = companies.find(c => c.id === selectedCompany);

  return (
    <div className="min-h-screen bg-slate-950" data-testid="dashboard">
      {/* Header */}
      <header className="bg-slate-900/50 border-b border-slate-800 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-[1920px] mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div 
                className="flex items-center gap-3 cursor-pointer hover:opacity-80 transition-opacity"
                onClick={() => navigate('/dashboard')}
              >
                <div className="w-10 h-10 bg-cyan-500/20 rounded-xl flex items-center justify-center border border-cyan-500/30">
                  <Shield className="w-5 h-5 text-cyan-400" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-white">Alert Whisperer</h1>
                  <p className="text-xs text-slate-400">Operations Intelligence</p>
                </div>
              </div>

              {/* Company Selector */}
              <div className="ml-8 flex items-center gap-3">
                <Select 
                  value={selectedCompany} 
                  onValueChange={(value) => {
                    setSelectedCompany(value);
                    localStorage.setItem('selectedCompany', value);
                  }}
                >
                  <SelectTrigger className="w-[250px] bg-slate-800/50 border-slate-700 text-white" data-testid="company-selector">
                    <SelectValue placeholder="Select company" />
                  </SelectTrigger>
                  <SelectContent className="bg-slate-800 border-slate-700">
                    {userCompanies.map((company) => (
                      <SelectItem key={company.id} value={company.id} className="text-white hover:bg-slate-700">
                        {company.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                
                {/* Demo Button */}
                <Button
                  onClick={() => setShowDemoModal(true)}
                  variant="outline"
                  size="sm"
                  className="bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700 text-white border-0"
                >
                  <Zap className="w-4 h-4 mr-2" />
                  Demo Mode
                </Button>
              </div>
            </div>

            <div className="flex items-center gap-4">
              {/* Notifications removed per user request */}

              {/* MSP Workflow Guide Button - Prominent */}
              <Button
                onClick={() => setShowMSPGuide(true)}
                size="sm"
                className="bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 text-white font-semibold border-0 shadow-lg"
              >
                <Zap className="w-4 h-4 mr-2" />
                📘 How MSPs Work
              </Button>

              <Button
                onClick={() => navigate('/help')}
                variant="outline"
                size="sm"
                className="border-slate-700 text-slate-300 hover:bg-slate-800 hover:text-white"
              >
                ❓ Help
              </Button>

              <Button
                onClick={() => navigate('/technicians')}
                variant="outline"
                size="sm"
                className="border-slate-700 text-slate-300 hover:bg-slate-800 hover:text-white"
              >
                <Settings className="w-4 h-4 mr-2" />
                Technicians
              </Button>

              <Button
                onClick={() => navigate('/runbooks')}
                variant="outline"
                size="sm"
                className="border-slate-700 text-slate-300 hover:bg-slate-800 hover:text-white"
              >
                <FileText className="w-4 h-4 mr-2" />
                Runbooks
              </Button>
              
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" className="text-white hover:bg-slate-800">
                    <div className="flex items-center gap-2">
                      <div className="w-8 h-8 bg-cyan-500/20 rounded-full flex items-center justify-center border border-cyan-500/30">
                        <User className="w-4 h-4 text-cyan-400" />
                      </div>
                      <div className="text-left">
                        <p className="text-sm font-medium">{user.name}</p>
                        <p className="text-xs text-slate-400">{user.role}</p>
                      </div>
                    </div>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent className="w-48 bg-slate-900 border-slate-800" align="end">
                  <DropdownMenuLabel className="text-slate-300">My Account</DropdownMenuLabel>
                  <DropdownMenuSeparator className="bg-slate-800" />
                  <DropdownMenuItem 
                    onClick={() => navigate('/profile')}
                    className="text-slate-300 focus:bg-slate-800 focus:text-white cursor-pointer"
                  >
                    <User className="w-4 h-4 mr-2" />
                    Profile Settings
                  </DropdownMenuItem>
                  <DropdownMenuSeparator className="bg-slate-800" />
                  <DropdownMenuItem 
                    onClick={onLogout}
                    className="text-red-400 focus:bg-red-500/10 focus:text-red-400 cursor-pointer"
                  >
                    <LogOut className="w-4 h-4 mr-2" />
                    Logout
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-[1920px] mx-auto px-6 py-6">
        {!selectedCompany ? (
          <Card className="bg-slate-900/50 border-slate-800">
            <CardContent className="py-12 text-center">
              <AlertTriangle className="w-12 h-12 text-slate-500 mx-auto mb-4" />
              <p className="text-slate-400">Please select a company to view operations</p>
            </CardContent>
          </Card>
        ) : (
          <>
            {/* KPI Overview */}
            <div className="mb-6">
              <KPIDashboard kpis={kpis} companyId={selectedCompany} onRefresh={loadKPIs} />
            </div>

            {/* Tabs */}
            <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
              <TabsList className="bg-slate-900/50 border border-slate-800 p-1">
                <TabsTrigger 
                  value="overview" 
                  className="data-[state=active]:bg-cyan-500/20 data-[state=active]:text-cyan-400"
                  data-testid="tab-overview"
                >
                  <Activity className="w-4 h-4 mr-2" />
                  Overview
                </TabsTrigger>
                <TabsTrigger 
                  value="impact" 
                  className="data-[state=active]:bg-cyan-500/20 data-[state=active]:text-cyan-400"
                  data-testid="tab-impact"
                >
                  <TrendingDown className="w-4 h-4 mr-2" />
                  Impact Analysis
                </TabsTrigger>
                <TabsTrigger 
                  value="correlation" 
                  className="data-[state=active]:bg-cyan-500/20 data-[state=active]:text-cyan-400"
                  data-testid="tab-correlation"
                >
                  <Zap className="w-4 h-4 mr-2" />
                  Alert Correlation
                </TabsTrigger>
                <TabsTrigger 
                  value="incidents" 
                  className="data-[state=active]:bg-cyan-500/20 data-[state=active]:text-cyan-400"
                  data-testid="tab-incidents"
                >
                  <AlertTriangle className="w-4 h-4 mr-2" />
                  Incidents
                </TabsTrigger>
                <TabsTrigger 
                  value="analysis" 
                  className="data-[state=active]:bg-cyan-500/20 data-[state=active]:text-cyan-400"
                  data-testid="tab-analysis"
                >
                  <TrendingDown className="w-4 h-4 mr-2" />
                  Analysis
                </TabsTrigger>
                <TabsTrigger 
                  value="asset-inventory" 
                  className="data-[state=active]:bg-cyan-500/20 data-[state=active]:text-cyan-400"
                >
                  <Server className="w-4 h-4 mr-2" />
                  Assets
                </TabsTrigger>
                <TabsTrigger 
                  value="runbooks" 
                  className="data-[state=active]:bg-cyan-500/20 data-[state=active]:text-cyan-400"
                >
                  <BookOpen className="w-4 h-4 mr-2" />
                  Runbooks
                </TabsTrigger>
                {(user.role === 'admin' || user.role === 'msp_admin') && (
                  <TabsTrigger 
                    value="companies" 
                    className="data-[state=active]:bg-cyan-500/20 data-[state=active]:text-cyan-400"
                    data-testid="tab-companies"
                  >
                    <Shield className="w-4 h-4 mr-2" />
                    Companies
                  </TabsTrigger>
                )}
              </TabsList>

              <TabsContent value="overview" className="space-y-6">
                {/* Button to scroll to How It Works */}
                <Card className="bg-gradient-to-r from-cyan-900/20 to-blue-900/20 border-cyan-500/30">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-lg font-semibold text-white mb-1">
                          Welcome to Alert Whisperer Dashboard
                        </h3>
                        <p className="text-sm text-slate-400">
                          Monitor all your alerts, incidents, and automation in real-time
                        </p>
                      </div>
                      <Button 
                        onClick={scrollToHowItWorks}
                        variant="outline"
                        className="border-cyan-500/30 text-cyan-400 hover:bg-cyan-500/10"
                      >
                        <BookOpen className="w-4 h-4 mr-2" />
                        See How It Works
                      </Button>
                    </div>
                  </CardContent>
                </Card>
                
                <RealTimeDashboard 
                  companyId={selectedCompany} 
                  companyName={currentCompany?.name}
                  refreshTrigger={refreshTrigger}
                />
                
                {/* Live KPI Proof with Before/After Comparison */}
                <div className="mt-8">
                  <h2 className="text-2xl font-bold text-white mb-4">Live KPI Proof & Impact Analysis</h2>
                  <p className="text-slate-400 mb-6">
                    Real-time calculations from production data • Not estimates or ranges
                  </p>
                  <LiveKPIProof companyId={selectedCompany} refreshTrigger={refreshTrigger} />
                </div>

                {/* How It Works Guide - Moved to Bottom */}
                <div ref={howItWorksRef} className="scroll-mt-6">
                  <HowItWorksGuide />
                </div>
              </TabsContent>

              <TabsContent value="impact" className="space-y-6">
                <KPIImpactDashboard companyId={selectedCompany} refreshTrigger={refreshTrigger} />
              </TabsContent>

              <TabsContent value="correlation">
                <AlertCorrelation companyId={selectedCompany} companyName={currentCompany?.name} refreshTrigger={refreshTrigger} />
              </TabsContent>

              <TabsContent value="incidents">
                <IncidentList companyId={selectedCompany} refreshTrigger={refreshTrigger} />
              </TabsContent>

              <TabsContent value="analysis" className="space-y-6">
                <IncidentAnalysis companyId={selectedCompany} refreshTrigger={refreshTrigger} />
              </TabsContent>

              <TabsContent value="asset-inventory">
                <AssetInventory companyId={selectedCompany} refreshTrigger={refreshTrigger} />
              </TabsContent>

              <TabsContent value="runbooks">
                <div className="space-y-6">
                  <CustomRunbookManager companyId={selectedCompany} refreshTrigger={refreshTrigger} />
                  
                  <div className="border-t border-slate-700 pt-6">
                    <div className="flex items-center justify-between mb-4">
                      <div>
                        <h3 className="text-xl font-bold text-white">Pre-Built Runbook Library</h3>
                        <p className="text-slate-400 text-sm">Browse and execute ready-made automation scripts</p>
                      </div>
                      <Button
                        onClick={() => navigate('/runbooks')}
                        className="bg-cyan-600 hover:bg-cyan-700"
                      >
                        <BookOpen className="w-4 h-4 mr-2" />
                        Browse Library
                      </Button>
                    </div>
                  </div>
                </div>
              </TabsContent>

              {(user.role === 'admin' || user.role === 'msp_admin') && (
                <TabsContent value="companies">
                  <CompanyManagement onCompanyChange={loadCompanies} />
                </TabsContent>
              )}
            </Tabs>
          </>
        )}
      </main>

      {/* MSP Workflow Guide Modal */}
      {showMSPGuide && (
        <MSPWorkflowGuide onClose={() => setShowMSPGuide(false)} />
      )}

      {/* Demo Mode Modal */}
      <DemoModeModal
        isOpen={showDemoModal}
        onClose={() => setShowDemoModal(false)}
        onDemoCompanySelected={handleDemoCompanySelected}
      />
    </div>
  );
};

export default Dashboard;