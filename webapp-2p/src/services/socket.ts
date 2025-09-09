import { io, Socket } from 'socket.io-client'

export function connectSocket(serverUrl: string): Socket {
  // Allow default transports (polling + websocket) for robust dev usage
  return io(serverUrl)
}

export type { Socket }

