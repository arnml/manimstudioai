import { useState, useEffect } from 'react';
import { Play, Code, Video, Edit3 } from 'lucide-react';
import Editor from '@monaco-editor/react';

export default function ContentPanel({ 
  currentView, 
  onViewChange, 
  code, 
  onCodeChange, 
  videoPath, 
  onRunCode, 
  isRunning 
}) {
  const [localCode, setLocalCode] = useState(code);

  useEffect(() => {
    setLocalCode(code);
  }, [code]);

  const handleCodeChange = (value) => {
    setLocalCode(value);
    onCodeChange(value);
  };

  const handleRunCode = () => {
    onRunCode(localCode);
  };

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Header with toggle buttons */}
      <div className="border-b border-gray-200 p-6 flex items-center justify-between bg-gray-50">
        <div className="flex items-center space-x-1">
          <button
            onClick={() => onViewChange('video')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors border-b-2 ${
              currentView === 'video'
                ? 'bg-white text-orange-700 border-orange-500 font-semibold shadow-sm'
                : 'text-gray-600 border-transparent hover:text-gray-900 hover:bg-gray-100'
            }`}
          >
            <Video className="w-4 h-4" />
            <span className="text-sm">Preview</span>
          </button>
          <button
            onClick={() => onViewChange('code')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors border-b-2 ${
              currentView === 'code'
                ? 'bg-white text-orange-700 border-orange-500 font-semibold shadow-sm'
                : 'text-gray-600 border-transparent hover:text-gray-900 hover:bg-gray-100'
            }`}
          >
            <Code className="w-4 h-4" />
            <span className="text-sm">Code</span>
          </button>
        </div>

        {currentView === 'code' && (
          <button
            onClick={handleRunCode}
            disabled={isRunning}
            className="flex items-center space-x-2 bg-orange-500 hover:bg-orange-600 disabled:bg-gray-400 text-white px-4 py-2 rounded-lg transition-colors shadow-sm"
          >
            <Play className="w-4 h-4" />
            <span className="text-sm">{isRunning ? 'Running...' : 'Run'}</span>
          </button>
        )}
      </div>

      {/* Content area */}
      <div className="flex-1 overflow-hidden">
        {currentView === 'video' ? (
          <VideoView videoPath={videoPath} />
        ) : (
          <CodeEditor 
            code={localCode} 
            onChange={handleCodeChange} 
          />
        )}
      </div>
    </div>
  );
}

function VideoView({ videoPath }) {
  if (!videoPath) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-50">
        <div className="text-center text-gray-500">
          <Video className="w-16 h-16 mx-auto mb-4 text-gray-300" />
          <p className="text-lg text-gray-700">No video generated yet</p>
          <p className="text-sm text-gray-500">Send a message to create your first animation</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex items-center justify-center bg-gray-50 p-8">
      <div className="bg-white rounded-lg shadow-lg border border-gray-200 p-4">
        <video
          src={`http://localhost:8000/${videoPath}`}
          controls
          className="max-w-full max-h-full rounded-lg"
          autoPlay
        />
      </div>
    </div>
  );
}

function CodeEditor({ code, onChange }) {
  return (
    <div className="h-full bg-gray-50 p-4">
      <div className="h-full bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
        <Editor
          height="100%"
          defaultLanguage="python"
          value={code}
          onChange={onChange}
          theme="vs"
          options={{
            minimap: { enabled: false },
            fontSize: 14,
            lineNumbers: 'on',
            roundedSelection: false,
            scrollBeyondLastLine: false,
            readOnly: false,
            automaticLayout: true,
            tabSize: 4,
            insertSpaces: true,
            wordWrap: 'on',
            lineHeight: 1.6,
            fontFamily: '"Courier New", Consolas, "Liberation Mono", monospace',
            padding: { top: 16, bottom: 16 },
          }}
        />
      </div>
    </div>
  );
}