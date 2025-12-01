import { useEffect, useState } from 'react';
import wsService from '../services/websocket';

export const useWebSocket = (autoConnect = true) => {
  const [connected, setConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);

  useEffect(() => {
    if (!autoConnect) return;

    const handleConnected = () => setConnected(true);
    const handleDisconnected = () => setConnected(false);
    const handleMessage = (data) => setLastMessage(data);

    wsService.on('connected', handleConnected);
    wsService.on('disconnected', handleDisconnected);
    wsService.on('optimization_update', handleMessage);

    wsService.connect();

    return () => {
      wsService.off('connected', handleConnected);
      wsService.off('disconnected', handleDisconnected);
      wsService.off('optimization_update', handleMessage);
    };
  }, [autoConnect]);

  return { connected, lastMessage, send: wsService.send.bind(wsService) };
};

export default useWebSocket;
