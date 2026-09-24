import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { Home, Shield, BookOpen, CheckCircle } from 'lucide-react';
import Dashboard from './pages/Dashboard';
import TrainingHub from './pages/TrainingHub';
import TrainingModule from './pages/TrainingModule';
import TrainingHistory from './pages/TrainingHistory';

// Using OP1003 for the demo
export const OPERATOR_ID = "OP1003";

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50 flex flex-col">
        {/* Top Navigation */}
        <nav className="bg-slate-900 text-white p-4 shadow-md">
          <div className="max-w-7xl mx-auto flex justify-between items-center">
            <div className="flex items-center space-x-2">
              <Shield className="text-yellow-500" size={28} />
              <span className="text-xl font-bold tracking-wider">CAT Smart Assistant</span>
            </div>
            <div className="flex space-x-6">
              <Link to="/" className="flex items-center space-x-2 hover:text-yellow-500 transition">
                <Home size={18} />
                <span>Dashboard</span>
              </Link>
              <Link to="/training" className="flex items-center space-x-2 hover:text-yellow-500 transition">
                <BookOpen size={18} />
                <span>Training Hub</span>
              </Link>
              <Link to="/history" className="flex items-center space-x-2 hover:text-yellow-500 transition">
                <CheckCircle size={18} />
                <span>History</span>
              </Link>
              <div className="flex items-center pl-6 border-l border-slate-700">
                <span className="text-sm text-slate-400 mr-2">Operator:</span>
                <span className="font-semibold">{OPERATOR_ID}</span>
              </div>
            </div>
          </div>
        </nav>

        {/* Main Content Area */}
        <main className="flex-grow max-w-7xl mx-auto w-full p-6">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/training" element={<TrainingHub />} />
            <Route path="/training/:moduleId" element={<TrainingModule />} />
            <Route path="/history" element={<TrainingHistory />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
