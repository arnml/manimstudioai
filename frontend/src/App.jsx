import { useState, useEffect } from 'react';
import io from 'socket.io-client';

const socket = io('http://localhost:8000');

function App() {
  const [prompt, setPrompt] = useState('');
  const [code, setCode] = useState('');
  const [videoPath, setVideoPath] = useState('');
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    socket.on('code_generated', (data) => {
      setCode(data.code);
      setStatus('Rendering Video...');
    });

    socket.on('video_rendered', (data) => {
      setVideoPath(data.video_path);
      setStatus('Video Ready');
    });

    socket.on('render_error', (data) => {
      setError(data.error);
      setStatus('Error');
    });

    return () => {
      socket.off('code_generated');
      socket.off('video_rendered');
      socket.off('render_error');
    };
  }, []);

  const handleSubmit = async () => {
    setStatus('Generating Code...');
    setError('');
    setVideoPath('');
    setCode('');

    try {
      await fetch('http://localhost:8000/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ prompt }),
      });
    } catch (error) {
      setError(error.message);
      setStatus('Error');
    }
  };

  return (
    <div className="bg-gray-900 text-white min-h-screen flex flex-col items-center justify-center">
      <div className="w-full max-w-2xl p-8">
        <h1 className="text-4xl font-bold text-center mb-8">Manim Studio AI</h1>
        <div className="bg-gray-800 p-4 rounded-lg mb-4">
          <textarea
            className="w-full bg-gray-700 text-white p-2 rounded-lg"
            rows="4"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Enter your animation prompt here..."
          />
          <button
            className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg mt-4 w-full"
            onClick={handleSubmit}
          >
            Generate
          </button>
        </div>
        <div className="bg-gray-800 p-4 rounded-lg">
          <h2 className="text-2xl font-bold mb-4">Status: {status}</h2>
          {error && (
            <div className="bg-red-500 p-4 rounded-lg mb-4">
              <p>{error}</p>
              <div className="flex justify-end mt-4">
                <button className="bg-yellow-500 hover:bg-yellow-600 text-white font-bold py-2 px-4 rounded-lg mr-2">
                  Update Prompt
                </button>
                <button className="bg-green-500 hover:bg-green-600 text-white font-bold py-2 px-4 rounded-lg">
                  Try to Fix
                </button>
              </div>
            </div>
          )}
          {code && (
            <pre className="bg-gray-700 p-4 rounded-lg mb-4 whitespace-pre-wrap">
              <code>{code}</code>
            </pre>
          )}
          {videoPath && (
            <video src={`http://localhost:8000/${videoPath}`} controls className="w-full rounded-lg" />
          )}
        </div>
      </div>
    </div>
  );
}

export default App;