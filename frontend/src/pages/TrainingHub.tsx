import { useEffect, useState } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';
import { BookOpen, Clock, ChevronRight, AlertTriangle } from 'lucide-react';
import { OPERATOR_ID } from '../App';
import { API_BASE_URL } from '../config';

interface Progress {
  completed: number;
  in_progress: number;
  recommended: number;
  training_time_minutes: number;
}

interface Module {
  module_id: string;
  title: string;
  category: string;
  description: string;
  duration_minutes: number;
  difficulty: string;
}

export default function TrainingHub() {
  const [progress, setProgress] = useState<Progress | null>(null);
  const [modules, setModules] = useState<Module[]>([]);
  const [recommendations, setRecommendations] = useState<any[]>([]);

  useEffect(() => {
    axios.get(`${API_BASE_URL}/api/training/progress/${OPERATOR_ID}`)
      .then(res => setProgress(res.data))
      .catch(err => console.error(err));

    axios.get(`${API_BASE_URL}/api/training/modules`)
      .then(res => setModules(res.data))
      .catch(err => console.error(err));

    axios.get(`${API_BASE_URL}/api/training/recommendations/${OPERATOR_ID}`)
      .then(res => setRecommendations(res.data))
      .catch(err => console.error(err));
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-end border-b border-slate-200 pb-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-800">Training Hub</h1>
          <p className="text-slate-500 mt-1">Enhance your skills based on your operational history.</p>
        </div>
      </div>

      {/* Progress Overview */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm text-center">
          <p className="text-sm text-slate-500 font-medium uppercase tracking-wide">Completed</p>
          <p className="text-3xl font-bold text-slate-800 mt-1">{progress?.completed || 0}</p>
        </div>
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm text-center">
          <p className="text-sm text-slate-500 font-medium uppercase tracking-wide">In Progress</p>
          <p className="text-3xl font-bold text-blue-600 mt-1">{progress?.in_progress || 0}</p>
        </div>
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm text-center">
          <p className="text-sm text-slate-500 font-medium uppercase tracking-wide">Recommended</p>
          <p className="text-3xl font-bold text-red-600 mt-1">{progress?.recommended || 0}</p>
        </div>
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm text-center">
          <p className="text-sm text-slate-500 font-medium uppercase tracking-wide">Training Time</p>
          <p className="text-3xl font-bold text-emerald-600 mt-1">{progress?.training_time_minutes || 0} <span className="text-lg">min</span></p>
        </div>
      </div>

      {/* Module List */}
      <div className="mt-8">
        <h2 className="text-xl font-bold text-slate-800 mb-4">Available Modules</h2>
        <div className="space-y-4">
          {modules.map(mod => {
            const isRecommended = recommendations.some(r => r.module.module_id === mod.module_id);
            return (
              <div key={mod.module_id} className={`bg-white p-6 rounded-xl shadow-sm border flex items-center ${isRecommended ? 'border-red-300 bg-red-50/30' : 'border-slate-200'}`}>
                <div className={`p-4 rounded-xl mr-6 ${isRecommended ? 'bg-red-100 text-red-600' : 'bg-slate-100 text-slate-600'}`}>
                  {isRecommended ? <AlertTriangle size={32} /> : <BookOpen size={32} />}
                </div>
                <div className="flex-grow">
                  <div className="flex items-center space-x-2">
                    <h3 className="text-lg font-bold text-slate-800">{mod.title}</h3>
                    {isRecommended && <span className="bg-red-500 text-white text-[10px] px-2 py-0.5 rounded-full font-bold">RECOMMENDED</span>}
                  </div>
                  <p className="text-slate-600 text-sm mt-1">{mod.description}</p>
                  <div className="flex space-x-4 mt-3">
                    <span className="text-xs font-medium text-slate-500 flex items-center">
                      <Clock size={14} className="mr-1" /> {mod.duration_minutes} min
                    </span>
                    <span className="text-xs font-medium text-slate-500 bg-slate-100 px-2 rounded">
                      {mod.difficulty}
                    </span>
                    <span className="text-xs font-medium text-slate-500 bg-slate-100 px-2 rounded">
                      {mod.category}
                    </span>
                  </div>
                </div>
                <div className="ml-4">
                  <Link 
                    to={`/training/${mod.module_id}`}
                    className={`px-6 py-3 rounded-lg text-sm font-bold flex items-center transition ${
                      isRecommended ? 'bg-red-600 hover:bg-red-700 text-white shadow-md' : 'bg-slate-900 hover:bg-slate-800 text-white'
                    }`}
                  >
                    Open <ChevronRight size={18} className="ml-1" />
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
