import { useEffect, useState } from 'react';
import axios from 'axios';
import { CheckCircle, Award } from 'lucide-react';
import { OPERATOR_ID } from '../App';
import { API_BASE_URL } from '../config';

interface HistoryItem {
  module_title: string;
  date: string;
  score: number;
  status: string;
}

export default function TrainingHistory() {
  const [history, setHistory] = useState<HistoryItem[]>([]);

  useEffect(() => {
    axios.get(`${API_BASE_URL}/api/training/history/${OPERATOR_ID}`)
      .then(res => setHistory(res.data))
      .catch(err => console.error(err));
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-end border-b border-slate-200 pb-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-800">Training History</h1>
          <p className="text-slate-500 mt-1">Review your completed modules and scores.</p>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        {history.length > 0 ? (
          <table className="min-w-full divide-y divide-slate-200">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Module</th>
                <th className="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Completion Date</th>
                <th className="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Score</th>
                <th className="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Status</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-slate-200">
              {history.map((item, idx) => (
                <tr key={idx} className="hover:bg-slate-50 transition">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <Award className="text-slate-400 mr-3" size={20} />
                      <span className="text-sm font-bold text-slate-800">{item.module_title}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="text-sm text-slate-600">{new Date(item.date).toLocaleDateString()}</span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="px-3 py-1 inline-flex text-xs leading-5 font-bold rounded-full bg-emerald-100 text-emerald-800">
                      {item.score}%
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center text-emerald-600">
                      <CheckCircle size={16} className="mr-1" />
                      <span className="text-sm font-medium">{item.status}</span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="p-12 text-center">
            <Award className="mx-auto text-slate-300 mb-4" size={48} />
            <p className="text-lg font-medium text-slate-600">No training history yet.</p>
            <p className="text-slate-500 mt-1">Complete your recommended modules to see them here.</p>
          </div>
        )}
      </div>
    </div>
  );
}
