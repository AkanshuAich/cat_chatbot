import React, { useState, useRef, useEffect } from 'react';
import { SendHorizontal } from 'lucide-react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card } from "@/components/ui/card";

const ChatInterface = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const scrollAreaRef = useRef(null);

  // Added auto scroll to bottom feature when new messages arrive
  useEffect(() => {
    if (scrollAreaRef.current) {
      const scrollArea = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]');
      if (scrollArea) {
        scrollArea.scrollTop = scrollArea.scrollHeight;
      }
    }
  }, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    // user message is added to chat
    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:5000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        mode: 'cors', // I have enabled CORS for cross-connection
        credentials: 'same-origin', 
        body: JSON.stringify({ message: input }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      // Add assistant response to chat
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.content,
        images: data.images || []
      }]);
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, there was an error connecting to the server. Please make sure the backend is running and try again.',
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const renderMessage = (message, index) => {
    const isUser = message.role === 'user';
    
    return (
      <div
        key={index}
        className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}
      >
        <div 
          className={`max-w-3xl ${isUser ? 'bg-blue-600' : 'bg-gray-700'} rounded-lg p-4`}
        >
          <p className="text-white whitespace-pre-wrap break-words">{message.content}</p>
          {message.images && message.images.map((image, imgIndex) => (
            <img
              key={imgIndex}
              src={image}
              alt={`Cat ${imgIndex + 1}`}
              className="mt-2 rounded-lg max-w-sm h-auto"
              loading="lazy"
            />
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="h-screen flex flex-col bg-gray-900 text-white p-4">
      <Card className="flex-1 bg-gray-800 border-gray-700 mb-4 overflow-hidden flex flex-col">
        <ScrollArea ref={scrollAreaRef} className="flex-1 p-4">
          <div className="space-y-4">
            {messages.map((message, index) => renderMessage(message, index))}
            {isLoading && (
              <div className="flex justify-start mb-4">
                <div className="bg-gray-700 rounded-lg p-4">
                  <p className="text-white">Thinking...</p>
                </div>
              </div>
            )}
          </div>
        </ScrollArea>
      </Card>
      
      <form onSubmit={handleSubmit} className="flex gap-2">
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about cats..."
          className="flex-1 bg-gray-800 border-gray-700 text-white"
          disabled={isLoading}
        />
        <Button 
          type="submit" 
          disabled={isLoading}
          className="bg-blue-600 hover:bg-blue-700"
        >
          <SendHorizontal className="h-5 w-5" />
        </Button>
      </form>
    </div>
  );
};

export default ChatInterface;