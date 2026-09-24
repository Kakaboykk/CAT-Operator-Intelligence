import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { ArrowLeft, CheckCircle, XCircle } from 'lucide-react';
import { OPERATOR_ID } from '../App';
import { API_BASE_URL } from '../config';

interface Question {
  question_id: string;
  question_text: string;
  options: string[];
}

interface ModuleData {
  module_id: string;
  title: string;
  description: string;
  questions: Question[];
}

export default function TrainingModule() {
  const { moduleId } = useParams();
  const navigate = useNavigate();

  const [moduleData, setModuleData] = useState<ModuleData | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [result, setResult] = useState<any | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    // Fetch module data
    axios.get(`${API_BASE_URL}/api/training/modules/${moduleId}`)
      .then(res => setModuleData(res.data))
      .catch(err => console.error(err));

    // Mark as started
    axios.post(`${API_BASE_URL}/api/training/modules/${moduleId}/start?operator_id=${OPERATOR_ID}`)
      .catch(err => console.error(err));
  }, [moduleId]);

  const handleOptionSelect = (questionId: string, option: string) => {
    setAnswers(prev => ({ ...prev, [questionId]: option }));
  };

  const handleSubmit = async () => {
    if (!moduleData || Object.keys(answers).length < moduleData.questions.length) {
      alert("Please answer all questions before submitting.");
      return;
    }

    setSubmitting(true);
    try {
      const res = await axios.post(
        `${API_BASE_URL}/api/training/modules/${moduleId}/quiz?operator_id=${OPERATOR_ID}`,
        { answers }
      );
      setResult(res.data);
    } catch (err) {
      console.error(err);
      alert("Error submitting quiz.");
    } finally {
      setSubmitting(false);
    }
  };

  if (!moduleData) return <div className="p-8 text-center text-slate-500">Loading Module...</div>;

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <button
        onClick={() => navigate('/training')}
        className="flex items-center text-slate-500 hover:text-slate-800 transition"
      >
        <ArrowLeft size={18} className="mr-1" /> Back to Training Hub
      </button>

      {!result ? (
        <>
          <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-200">
            <h1 className="text-3xl font-bold text-slate-900 mb-4">{moduleData.title}</h1>
            <div className="prose prose-slate max-w-none">
              <p className="text-lg text-slate-700 leading-relaxed">{moduleData.description}</p>

              <div className="my-8 p-6 bg-slate-50 border border-slate-200 rounded-xl">
                <h3 className="text-lg font-bold text-slate-800 mb-2">Scenario</h3>
                <p className="text-slate-700">
                  You are operating an excavator on a slight incline. The loading truck approaches, and you prepare to swing the boom. Suddenly, the machine shifts unexpectedly on the loose terrain. Without a seatbelt, the sudden jolt throws you forward against the controls, causing an uncontrolled movement of the bucket and risking a severe accident.
                </p>
                <h3 className="text-lg font-bold text-slate-800 mt-6 mb-2">Key Protocol</h3>
                <ul className="list-disc pl-5 text-slate-700 space-y-2">
                  <li>Inspect seatbelt webbing and latch daily.</li>
                  <li>Fasten seatbelt securely before starting the engine.</li>
                  <li>Never unfasten the seatbelt while the machine is in operation or in gear.</li>
                </ul>
              </div>
            </div>
          </div>

          <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-200">
            <h2 className="text-2xl font-bold text-slate-900 mb-6">Knowledge Check</h2>

            <div className="space-y-8">
              {moduleData.questions.map((q, idx) => (
                <div key={q.question_id} className="bg-slate-50 p-6 rounded-xl border border-slate-200">
                  <p className="font-bold text-slate-800 mb-4">
                    <span className="text-slate-400 mr-2">{idx + 1}.</span>
                    {q.question_text}
                  </p>
                  <div className="space-y-3">
                    {q.options.map((opt, oIdx) => (
                      <label key={oIdx} className={`flex items-center p-3 border rounded-lg cursor-pointer transition ${answers[q.question_id] === opt ? 'border-blue-500 bg-blue-50' : 'border-slate-200 bg-white hover:bg-slate-50'}`}>
                        <input
                          type="radio"
                          name={q.question_id}
                          value={opt}
                          checked={answers[q.question_id] === opt}
                          onChange={() => handleOptionSelect(q.question_id, opt)}
                          className="mr-3 h-4 w-4 text-blue-600 focus:ring-blue-500"
                        />
                        <span className="text-slate-700">{opt}</span>
                      </label>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-8 pt-6 border-t border-slate-200 flex justify-end">
              <button
                onClick={handleSubmit}
                disabled={submitting}
                className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-8 rounded-xl shadow-md transition disabled:opacity-50"
              >
                {submitting ? 'Grading...' : 'Submit Answers'}
              </button>
            </div>
          </div>
        </>
      ) : (
        <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-200 text-center">
          <div className={`mx-auto w-24 h-24 rounded-full flex items-center justify-center mb-6 ${result.passed ? 'bg-emerald-100 text-emerald-600' : 'bg-red-100 text-red-600'}`}>
            {result.passed ? <CheckCircle size={48} /> : <XCircle size={48} />}
          </div>
          <h2 className="text-3xl font-bold text-slate-900 mb-2">
            {result.passed ? 'Module Completed!' : 'Module Failed'}
          </h2>
          <p className="text-xl text-slate-600 mb-8">You scored <span className="font-bold text-slate-900">{result.score}%</span></p>

          <div className="text-left space-y-6 mb-8">
            {result.results.map((r: any, idx: number) => (
              <div key={r.question_id} className={`p-6 rounded-xl border ${r.is_correct ? 'border-emerald-200 bg-emerald-50' : 'border-red-200 bg-red-50'}`}>
                <div className="flex items-start">
                  <div className="mr-3 mt-1">
                    {r.is_correct ? <CheckCircle className="text-emerald-600" size={20} /> : <XCircle className="text-red-600" size={20} />}
                  </div>
                  <div>
                    <p className="font-bold text-slate-800 mb-2">Question {idx + 1}</p>
                    {!r.is_correct && (
                      <p className="text-sm text-red-700 mb-2">
                        <span className="font-bold">Your answer:</span> {r.selected_answer}
                      </p>
                    )}
                    <p className="text-sm text-slate-700">
                      <span className="font-bold">Correct answer:</span> {r.correct_answer}
                    </p>
                    <p className="text-sm text-slate-600 italic mt-3 pt-3 border-t border-slate-200/50">
                      {r.explanation}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <button
            onClick={() => navigate('/history')}
            className="bg-slate-900 hover:bg-slate-800 text-white font-bold py-3 px-8 rounded-xl shadow-md transition"
          >
            View Training History
          </button>
        </div>
      )}
    </div>
  );
}
