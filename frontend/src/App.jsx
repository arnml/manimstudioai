import { useState, useEffect } from 'react';
import io from 'socket.io-client';
import ChatPanel from './components/ChatPanel';
import ContentPanel from './components/ContentPanel';
import './App.css';

const socket = io(import.meta.env.VITE_API_URL || 'http://localhost:8000');

function App() {
  const [messages, setMessages] = useState([
    {
      role: 'user',
      content: 'Animate the step-by-step solution for the equation 2x + 3 = 7',
      timestamp: Date.now()
    }
  ]);
  const [currentView, setCurrentView] = useState('video');
  const [code, setCode] = useState('');
  const [videoPath, setVideoPath] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isRunning, setIsRunning] = useState(false);

  useEffect(() => {
    socket.on('code_generated', (data) => {
      setCode(data.code);
      setIsLoading(false);
      setIsRunning(true);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Code generated! Rendering video...',
        timestamp: Date.now()
      }]);
    });

    socket.on('video_rendered', (data) => {
      setVideoPath(data.video_path);
      setIsRunning(false);
      setMessages(prev => {
        const newMessages = [...prev];
        const lastMessage = newMessages[newMessages.length - 1];
        if (lastMessage?.role === 'assistant') {
          lastMessage.content = 'Animation rendered successfully! You can view it in the Preview tab or edit the code.';
        }
        return newMessages;
      });
    });

    socket.on('render_error', (data) => {
      setIsRunning(false);
      setIsLoading(false);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Error rendering animation: ${data.error}`,
        timestamp: Date.now()
      }]);
    });

    return () => {
      socket.off('code_generated');
      socket.off('video_rendered');
      socket.off('render_error');
    };
  }, []);

  const handleSendMessage = async (prompt) => {
    setMessages(prev => [...prev, {
      role: 'user',
      content: prompt,
      timestamp: Date.now()
    }]);

    setIsLoading(true);
    setVideoPath('');
    setCode('');

    try {
      await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt }),
      });
    } catch (error) {
      setIsLoading(false);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Error: ${error.message}`,
        timestamp: Date.now()
      }]);
    }
  };

  const handleRunCode = async (codeToRun) => {
    if (!codeToRun.trim()) return;

    setIsRunning(true);
    setVideoPath('');
    setMessages(prev => [...prev, {
      role: 'assistant',
      content: 'Running updated code...',
      timestamp: Date.now()
    }]);

    try {
      await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/render-code`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: codeToRun }),
      });
    } catch (error) {
      setIsRunning(false);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Error running code: ${error.message}`,
        timestamp: Date.now()
      }]);
    }
  };

  return (
    <div className="flex h-screen bg-gray-900 text-white font-sans">
      {/* Left Panel - Chat */}
      <div className="w-1/3 min-w-[400px] bg-transparent">
        <ChatPanel
          messages={messages}
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
        />
      </div>

      {/* Right Panel - Content */}
      <div className="flex-1 bg-transparent">
        <ContentPanel
          currentView={currentView}
          onViewChange={setCurrentView}
          code={code}
          onCodeChange={setCode}
          videoPath={videoPath}
          onRunCode={handleRunCode}
          isRunning={isRunning}
        />
      </div>
    </div>
  );
}

export default App;
