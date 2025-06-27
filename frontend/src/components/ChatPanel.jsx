import { useState } from 'react';
import { Send, Loader2 } from 'lucide-react';

export default function ChatPanel({ messages, onSendMessage, isLoading }) {
  const [prompt, setPrompt] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (prompt.trim() && !isLoading) {
      onSendMessage(prompt.trim());
      setPrompt('');
    }
  };

  return (
    <div className="flex flex-col h-full bg-transparent p-4">
      {/* Header */}
      <div className="flex-shrink-0 p-4">
        <h1 className="text-xl font-bold text-white">Manim Studio AI</h1>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-6 p-4">
        {messages.map((message, index) => (
          <div key={index} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-lg px-5 py-3 rounded-2xl ${
                message.role === 'user'
                  ? 'bg-white/10 text-white'
                  : 'bg-brand-purple-light/50 text-brand-gray-200'
              } backdrop-blur-xl border border-white/10 shadow-lg`}
            >
              <p className="text-sm">{message.content}</p>
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="max-w-lg px-5 py-3 rounded-2xl bg-brand-purple-light/50 text-brand-gray-200 backdrop-blur-xl border border-white/10 shadow-lg flex items-center space-x-3">
              <Loader2 className="w-5 h-5 animate-spin text-brand-teal" />
              <span>Generating...</span>
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="flex-shrink-0 p-4">
        <form onSubmit={handleSubmit} className="relative">
          <input
            type="text"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Send a message..."
            className="w-full bg-white/5 text-white border border-white/10 rounded-xl px-4 py-3 pr-12 focus:outline-none focus:ring-2 focus:ring-brand-teal transition-all"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={!prompt.trim() || isLoading}
            className="absolute right-2 top-1/2 transform -translate-y-1/2 bg-brand-teal hover:bg-brand-teal/80 disabled:bg-gray-500/50 text-brand-purple p-2 rounded-lg transition-colors"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
