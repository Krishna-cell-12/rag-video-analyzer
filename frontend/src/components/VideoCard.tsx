import React from 'react';

export interface VideoData {
  video_id: string;
  platform: string;
  creator: string;
  views: number;
  likes: number;
  comments: number;
  engagement_rate: number;
}

interface VideoCardProps {
  title: string;
  data: VideoData | null;
  isLoading: boolean;
}

export default function VideoCard({ title, data, isLoading }: VideoCardProps) {
  // If the backend is still processing, show a loading skeleton
  if (isLoading) {
    return (
      <div className="w-full bg-white rounded-xl shadow-sm border border-gray-200 p-6 animate-pulse">
        <div className="h-6 bg-gray-200 rounded w-1/3 mb-6"></div>
        <div className="space-y-4">
          <div className="h-4 bg-gray-200 rounded w-3/4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>
    );
  }

  // If no data is present yet, show an empty state
  if (!data) {
    return (
      <div className="w-full h-full min-h-[180px] bg-gray-50 rounded-xl border border-dashed border-gray-300 flex items-center justify-center p-6 text-center">
        <p className="text-gray-400 font-medium text-sm">Waiting for {title} URL extraction...</p>
      </div>
    );
  }

  const isYouTube = data.platform.toLowerCase() === 'youtube';
  const badgeColor = isYouTube ? 'bg-red-100 text-red-600' : 'bg-pink-100 text-pink-600';

  return (
    <div className="w-full bg-white rounded-xl shadow-sm border border-gray-200 p-6 flex flex-col gap-4 transition-all hover:shadow-md">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-bold text-gray-800">{title}</h3>
        <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${badgeColor}`}>
          {data.platform}
        </span>
      </div>

      <div className="border-b border-gray-100 pb-4">
        <p className="text-xs text-gray-500 uppercase tracking-wide">Creator</p>
        <p className="font-semibold text-gray-900 truncate">{data.creator}</p>
        <p className="text-xs text-gray-400 mt-1">ID: {data.video_id}</p>
      </div>

      <div className="grid grid-cols-2 gap-3 pt-2">
        <div className="bg-gray-50 rounded-lg p-3">
          <p className="text-xs text-gray-500 font-medium">Views</p>
          <p className="font-bold text-gray-900 text-sm">{data.views.toLocaleString()}</p>
        </div>
        <div className="bg-blue-50 rounded-lg p-3 border border-blue-100">
          <p className="text-xs text-blue-600 font-medium">Engagement</p>
          <p className="font-bold text-blue-700 text-base">{data.engagement_rate}%</p>
        </div>
        <div className="bg-gray-50 rounded-lg p-3">
          <p className="text-xs text-gray-500 font-medium">Likes</p>
          <p className="font-semibold text-gray-700 text-sm">{data.likes.toLocaleString()}</p>
        </div>
        <div className="bg-gray-50 rounded-lg p-3">
          <p className="text-xs text-gray-500 font-medium">Comments</p>
          <p className="font-semibold text-gray-700 text-sm">{data.comments.toLocaleString()}</p>
        </div>
      </div>
    </div>
  );
}