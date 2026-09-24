import { useEffect, useState } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';
import {
  AlertCircle,
  Clock,
  CheckCircle,
  Activity,
  ChevronRight
} from 'lucide-react';
import { OPERATOR_ID } from '../App';
import { API_BASE_URL } from '../config';

interface DashboardStats {
  operator_id: string;
  current_task_title?: string | null;
  current_task_time?: string | null;
  machine_status?: string | null;
  safety_status?: string | null;
}

interface Recommendation {
  module: {
    module_id: string;
    title: string;
    duration_minutes: number;
  };
  reason: string;
  priority: string;
}

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [statsLoading, setStatsLoading] = useState(true);
  const [recommendationsLoading, setRecommendationsLoading] = useState(true);
  const [statsError, setStatsError] = useState(false);
  const [recommendationsError, setRecommendationsError] = useState(false);

  useEffect(() => {
    // Fetch real dashboard data
    axios
      .get(`${API_BASE_URL}/api/dashboard/${OPERATOR_ID}`)
      .then((res) => {
        setStats(res.data);
      })
      .catch((err) => {
        console.error('Error fetching dashboard stats:', err);
        setStatsError(true);
      })
      .finally(() => {
        setStatsLoading(false);
      });

    // Fetch real training recommendations
    axios
      .get(`${API_BASE_URL}/api/training/recommendations/${OPERATOR_ID}`)
      .then((res) => {
        setRecommendations(res.data);
      })
      .catch((err) => {
        console.error('Error fetching training recommendations:', err);
        setRecommendationsError(true);
      })
      .finally(() => {
        setRecommendationsLoading(false);
      });
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-slate-800">
        Operator Dashboard
      </h1>

      {/* Real Data Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

        {/* Current Schedule */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100 flex items-center space-x-4">
          <div className="p-3 bg-blue-50 text-blue-600 rounded-lg">
            <Clock size={24} />
          </div>

          <div>
            <p className="text-sm text-slate-500 font-medium">
              Current Schedule
            </p>

            {statsLoading ? (
              <p className="text-lg font-medium text-slate-500">
                Loading...
              </p>
            ) : statsError ? (
              <p className="text-lg font-medium text-red-600">
                Unable to load
              </p>
            ) : stats?.current_task_title ? (
              <>
                <p className="text-lg font-bold text-slate-800">
                  {stats.current_task_title}
                </p>

                {stats.current_task_time && (
                  <p className="text-xs text-slate-400">
                    {stats.current_task_time}
                  </p>
                )}
              </>
            ) : (
              <p className="text-lg font-medium text-slate-600">
                No scheduled tasks
              </p>
            )}
          </div>
        </div>

        {/* Machine Status */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100 flex items-center space-x-4">
          <div className="p-3 bg-indigo-50 text-indigo-600 rounded-lg">
            <Activity size={24} />
          </div>

          <div>
            <p className="text-sm text-slate-500 font-medium">
              Machine Status
            </p>

            {statsLoading ? (
              <p className="text-lg font-medium text-slate-500">
                Loading...
              </p>
            ) : statsError ? (
              <p className="text-lg font-medium text-red-600">
                Unable to load
              </p>
            ) : (
              <p className="text-lg font-bold text-slate-800">
                {stats?.machine_status || 'No machine status available'}
              </p>
            )}
          </div>
        </div>

        {/* Safety Status */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100 flex items-center space-x-4">
          <div className="p-3 bg-emerald-50 text-emerald-600 rounded-lg">
            <CheckCircle size={24} />
          </div>

          <div>
            <p className="text-sm text-slate-500 font-medium">
              Recent Safety Status
            </p>

            {statsLoading ? (
              <p className="text-lg font-medium text-slate-500">
                Loading...
              </p>
            ) : statsError ? (
              <p className="text-lg font-medium text-red-600">
                Unable to load
              </p>
            ) : (
              <p className="text-lg font-bold text-slate-800">
                {stats?.safety_status || 'No recent safety data'}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Recommended Training */}
      <div className="mt-8">
        <h2 className="text-xl font-bold text-slate-800 mb-4">
          Recommended Training
        </h2>

        {recommendationsLoading ? (
          <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100 text-center">
            <p className="text-slate-500">
              Checking training recommendations...
            </p>
          </div>
        ) : recommendationsError ? (
          <div className="bg-white p-6 rounded-xl shadow-sm border border-red-100 text-center">
            <AlertCircle
              className="mx-auto text-red-500 mb-2"
              size={32}
            />

            <p className="text-red-600 font-medium">
              Unable to load training recommendations.
            </p>

            <p className="text-sm text-slate-500 mt-1">
              Please check that the backend is running.
            </p>
          </div>
        ) : recommendations.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {recommendations.map((rec) => (
              <div
                key={rec.module.module_id}
                className="bg-white p-6 rounded-xl shadow-sm border-l-4 border-l-red-500 border-t border-r border-b border-slate-100 relative overflow-hidden"
              >
                <div className="absolute top-0 right-0 bg-red-100 text-red-700 text-xs font-bold px-3 py-1 rounded-bl-lg">
                  {rec.priority} PRIORITY
                </div>

                <div className="flex items-start space-x-4 mt-2">
                  <div className="p-2 bg-red-50 text-red-600 rounded-full">
                    <AlertCircle size={24} />
                  </div>

                  <div className="flex-grow">
                    <h3 className="text-lg font-bold text-slate-800">
                      {rec.module.title}
                    </h3>

                    <p className="text-sm text-slate-600 mt-1">
                      {rec.reason}
                    </p>

                    <div className="mt-4 flex justify-between items-center">
                      <span className="text-xs font-medium text-slate-500 flex items-center">
                        <Clock size={14} className="mr-1" />
                        {rec.module.duration_minutes} min
                      </span>

                      <Link
                        to={`/training/${rec.module.module_id}`}
                        className="bg-slate-900 text-white px-4 py-2 rounded-lg text-sm font-medium flex items-center hover:bg-slate-800 transition"
                      >
                        Start Training
                        <ChevronRight size={16} className="ml-1" />
                      </Link>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100 text-center">
            <CheckCircle
              className="mx-auto text-emerald-500 mb-2"
              size={32}
            />

            <p className="text-slate-600 font-medium">
              You are all caught up! No required training at this time.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}