'use client';

import { useState } from 'react';
import VideoCard, { VideoData } from '../components/VideoCard';
import ChatPanel, { Message } from '../components/ChatPanel';

export default function Home() {
  // Input State
  const [urlA, setUrlA] = useState('');
  const [urlB, setUrlB] = useState('');
  
  // Data State
  const [videoA, setVideoA] = useState<VideoData | null>(null);
  const [videoB, setVideoB] = useState<VideoData | null>(null);
  const [isExtracting, setIsExtracting] = useState(false);
  const [error, setError] = useState('');

  // Chat State
  const [messages, setMessages] = useState<Message[]>([]);
  const [isChatting, setIsChatting] = useState(false);

  const handleExtract = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!urlA || !urlB) return setError("Please provide both URLs.");
    
    setIsExtracting(true);
    setError('');
    
    try {
      const res = await fetch('http://127.0.0.1:8000/api/extract', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url_a: urlA, url_b: urlB })
      });
      
      const json = await res.json();
      if (!res.ok) throw new Error(json.detail || "Extraction failed");
      
      setVideoA(json.data.video_a);
      setVideoB(json.data.video_b);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsExtracting(false);
    }
  };

  const handleSendMessage = async (userMessage: string) => {
    if (!videoA || !videoB) return setError("Please extract videos first.");
    
    const newMessages: Message[] = [...messages, { role: 'user', content: userMessage }];
    setMessages(newMessages);
    setIsChatting(true);

    try {
      const res = await fetch('http://127.0.0.1:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: newMessages,
          video_ids: [videoA.video_id, videoB.video_id]
        })
      });

      const json = await res.json();
      if (!res.ok) throw new Error(json.detail || "Chat failed");

      setMessages([...newMessages, { role: 'assistant', content: json.response }]);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsChatting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 p-6 font-sans">
      <div className="max-w-7xl mx-auto space-y-6">
        
        {/* Header */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
          <h1 className="text-2xl font-extrabold text-gray-900 tracking-tight">Social Analyst RAG</h1>
          <p className="text-gray-500 text-sm mt-1">Provide a YouTube and Instagram URL to compute metrics and query transcripts.</p>
        </div>

        {error && <div className="bg-red-50 text-red-600 p-4 rounded-lg text-sm border border-red-200">{error}</div>}

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 h-[calc(100vh-200px)] min-h-[700px]">
          
          {/* Left Side: Inputs and Cards */}
          <div className="lg:col-span-5 flex flex-col gap-6 h-full overflow-y-auto pr-2">
            <form onSubmit={handleExtract} className="bg-white p-6 rounded-xl shadow-sm border border-gray-200 flex flex-col gap-4">
              <div>
                <label className="block text-xs font-bold text-gray-700 uppercase mb-2">Video A URL</label>
                <input type="text" value={urlA} onChange={(e) => setUrlA(e.target.value)} className="w-full border border-gray-300 rounded-lg px-4 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none text-black" placeholder="https://youtube.com/..." />
              </div>
              <div>
                <label className="block text-xs font-bold text-gray-700 uppercase mb-2">Video B URL</label>
                <input type="text" value={urlB} onChange={(e) => setUrlB(e.target.value)} className="w-full border border-gray-300 rounded-lg px-4 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none text-black" placeholder="https://instagram.com/reel/..." />
              </div>
              <button type="submit" disabled={isExtracting} className="w-full bg-black text-white font-semibold py-2.5 rounded-lg hover:bg-gray-800 disabled:opacity-50 transition-colors mt-2">
                {isExtracting ? 'Extracting & Vectorizing...' : 'Analyze Videos'}
              </button>
            </form>

            <VideoCard title="Video A" data={videoA} isLoading={isExtracting} />
            <VideoCard title="Video B" data={videoB} isLoading={isExtracting} />
          </div>

          {/* Right Side: Chat */}
          <div className="lg:col-span-7 h-full">
            <ChatPanel messages={messages} onSendMessage={handleSendMessage} isLoading={isChatting} />
          </div>

        </div>
      </div>
    </div>
  );
}