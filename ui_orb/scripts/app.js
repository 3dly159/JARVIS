// JARVIS Orb UI - Pure ORB visualization with WebSocket state updates

class JarvisOrbUI {
    constructor() {
        this.canvas = document.getElementById('orbCanvas');
        this.ctx = this.canvas.getContext('2d');
        this.orbStatus = document.getElementById('orbStatus');
        this.transcriptInner = document.getElementById('transcriptInner');
        this.bootOverlay = document.getElementById('bootOverlay');
        this.bootStatus = document.getElementById('bootStatus');
        this.bootEngine = document.getElementById('bootEngine');
        this.connectionDot = document.getElementById('connectionDot');
        this.connectionLabel = document.getElementById('connectionLabel');
        
        // State tracking
        this.state = 'idle'; // idle, wake, listening, speaking, thinking, processing
        this.pulsePhase = 0;
        this.audioChunks = [];
        this.isRecording = false;
        this.mediaRecorder = null;
        
        // WebSocket connection
        this.ws = null;
        this.wsUrl = 'ws://localhost:18789'; // Will be updated from settings
        
        // Initialize
        this.init();
    }
    
    init() {
        // Set canvas size
        this.resizeCanvas();
        window.addEventListener('resize', () => this.resizeCanvas());
        
        // Boot sequence
        this.bootSequence();
        
        // Orb click handler (push-to-talk)
        this.canvas.addEventListener('mousedown', () => this.startListening());
        this.canvas.addEventListener('mouseup', () => this.stopListening());
        this.canvas.addEventListener('touchstart', (e) => {
            e.preventDefault();
            this.startListening();
        });
        this.canvas.addEventListener('touchend', (e) => {
            e.preventDefault();
            this.stopListening();
        });
        
        // Settings button
        document.getElementById('settingsBtn').addEventListener('click', () => {
            document.getElementById('settingsModal').style.display = 'block';
        });
        
        document.getElementById('closeSettings').addEventListener('click', () => {
            document.getElementById('settingsModal').style.display = 'none';
        });
        
        // Save settings
        document.getElementById('saveSettings').addEventListener('click', () => {
            this.saveSettings();
            document.getElementById('settingsModal').style.display = 'none';
        });
        
        // Fullscreen button
        document.getElementById('fullscreenBtn').addEventListener('click', () => {
            if (!document.fullscreenElement) {
                document.documentElement.requestFullscreen();
            } else {
                if (document.exitFullscreen) {
                    document.exitFullscreen();
                }
            }
        });
        
        // Start animation loop
        this.animate();
        
        // Connect WebSocket
        this.connectWebSocket();
    }
    
    resizeCanvas() {
        this.canvas.width = window.innerWidth * 0.8;
        this.canvas.height = window.innerHeight * 0.6;
        // Max size constraint
        const maxSize = Math.min(window.innerWidth * 0.8, window.innerHeight * 0.6, 400);
        this.canvas.width = Math.min(this.canvas.width, maxSize);
        this.canvas.height = Math.min(this.canvas.height, maxSize);
    }
    
    bootSequence() {
        const steps = [
            { text: 'INITIALIZING NEURAL CORES...', engine: 'READYING STT/TTS' },
            { text: 'LOADING PERSONALITY MATRIX...', engine: 'CALIBRATING EMOTIONAL RESPONSE' },
            { text: 'ESTABLISHING SECURE CHANNEL...', engine: 'INITIALIZING QUANTUM ENCRYPTION' },
            { text: 'SYSTEM INTEGRITY CHECK...', engine: 'ALL SUBSYSTEMS NOMINAL' },
            { text: 'ACTIVATING SENSORY ARRAY...', engine: 'ONLINE AND AWAITING COMMAND' }
        ];
        
        let step = 0;
        const bootInterval = setInterval(() => {
            if (step < steps.length) {
                this.bootStatus.textContent = steps[step].text;
                this.bootEngine.textContent = steps[step].engine;
                
                // Update progress bar
                const progress = document.getElementById('bootProgress');
                progress.style.width = ((step + 1) / steps.length * 100) + '%';
                
                step++;
            } else {
                clearInterval(bootInterval);
                // Fade out boot overlay
                setTimeout(() => {
                    this.bootOverlay.style.opacity = '0';
                    setTimeout(() => {
                        this.bootOverlay.style.display = 'none';
                    }, 600);
                }, 500);
                
                // Update connection status
                this.updateConnectionStatus('connecting');
            }
        }, 1500);
    }
    
    updateConnectionStatus(status) {
        switch(status) {
            case 'connecting':
                this.connectionDot.style.background = '#ffaa00';
                this.connectionLabel.textContent = 'CONNECTING...';
                break;
            case 'connected':
                this.connectionDot.style.background = '#00ff88';
                this.connectionLabel.textContent = 'ONLINE';
                break;
            case 'disconnected':
                this.connectionDot.style.background = '#ff4444';
                this.connectionLabel.textContent = 'OFFLINE';
                break;
        }
    }
    
    connectWebSocket() {
        try {
            this.ws = new WebSocket(this.wsUrl);
            
            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.updateConnectionStatus('connected');
            };
            
            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    if (data.type === 'state') {
                        this.setState(data.state);
                    } else if (data.type === 'transcript') {
                        this.addTranscriptMessage(data.role, data.content);
                    }
                } catch (e) {
                    console.error('Error parsing WebSocket message:', e);
                }
            };
            
            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                this.updateConnectionStatus('disconnected');
                // Attempt reconnection after delay
                setTimeout(() => this.connectWebSocket(), 3000);
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateConnectionStatus('disconnected');
            };
        } catch (e) {
            console.error('Failed to create WebSocket:', e);
            this.updateConnectionStatus('disconnected');
        }
    }
    
    setState(newState) {
        this.state = newState;
        this.orbStatus.textContent = this.getStateLabel(newState);
    }
    
    getStateLabel(state) {
        const labels = {
            'idle': 'SAY "HEY FRIDAY" TO BEGIN',
            'wake': 'DETECTING WAKE WORD...',
            'listening': 'LISTENING...',
            'speaking': 'SPEAKING...',
            'thinking': 'THINKING...',
            'processing': 'PROCESSING...'
        };
        return labels[state] || 'UNKNOWN STATE';
    }
    
    startListening() {
        if (this.isRecording) return;
        
        this.isRecording = true;
        this.setState('listening');
        
        // Request microphone access
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
                this.mediaRecorder = new MediaRecorder(stream, {
                    mimeType: 'audio/webm;codecs=opus'
                });
                
                this.audioChunks = [];
                
                this.mediaRecorder.ondataavailable = (event) => {
                    if (event.data.size > 0) {
                        this.audioChunks.push(event.data);
                    }
                };
                
                this.mediaRecorder.onstop = () => {
                    this.sendAudioToServer();
                };
                
                this.mediaRecorder.start(100); // Collect data every 100ms
            })
            .catch(err => {
                console.error('Mic access denied:', err);
                this.isRecording = false;
                this.setState('idle');
                this.addTranscriptMessage('system', 'Microphone access denied. Please check permissions.');
            });
    }
    
    stopListening() {
        if (!this.isRecording || !this.mediaRecorder) return;
        
        this.isRecording = false;
        this.mediaRecorder.stop();
        
        // Get tracks and stop them
        const stream = this.mediaRecorder.stream;
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
        }
        
        this.setState('processing');
    }
    
    sendAudioToServer() {
        if (this.audioChunks.length === 0) {
            this.setState('idle');
            return;
        }
        
        const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
        const formData = new FormData();
        formData.append('file', audioBlob, 'audio.webm');
        
        fetch('http://localhost:8080/api/voice/transcribe', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Transcription error:', data.error);
                this.addTranscriptMessage('system', `Error: ${data.error}`);
            } else if (data.text) {
                // Send transcript to server for processing
                this.addTranscriptMessage('user', data.text);
                // TODO: Send to JARVIS brain for processing
                this.setState('thinking');
                
                // Simulate processing delay then get response
                setTimeout(() => {
                    this.getJarvisResponse(data.text);
                }, 1000);
            }
            this.setState('idle');
        })
        .catch(err => {
            console.error('Fetch error:', err);
            this.addTranscriptMessage('system', 'Network error. Please check connection.');
            this.setState('idle');
        });
    }
    
    getJarvisResponse(userInput) {
        // This would normally go through the JARVIS brain
        // For now, simulate a response
        const responses = [
            "I understand. Let me process that request.",
            "One moment while I analyze the situation.",
            "Processing your command now.",
            "Working on it, sir.",
            "I'll handle that immediately."
        ];
        
        const response = responses[Math.floor(Math.random() * responses.length)];
        this.addTranscriptMessage('assistant', response);
        
        // Speak the response
        this.speakResponse(response);
        
        // After speaking, go back to idle
        setTimeout(() => {
            this.setState('idle');
        }, 3000);
    }
    
    speakResponse(text) {
        this.setState('speaking');
        
        fetch('http://localhost:8080/api/voice/speak', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ text: text })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('TTS request failed');
            }
            return response.blob();
        })
        .then(blob => {
            const audioUrl = window.URL.createObjectURL(blob);
            const audio = new Audio(audioUrl);
            audio.play();
            
            audio.onended = () => {
                window.URL.revokeObjectURL(audioUrl);
            };
        })
        .catch(err => {
            console.error('TTS error:', err);
            this.setState('idle');
        });
    }
    
    addTranscriptMessage(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `transcript-message ${role}`;
        
        const header = document.createElement('div');
        header.className = 'transcript-header';
        header.textContent = role.toUpperCase() + ' · ' + new Date().toLocaleTimeString('en-GB', { hour12: false });
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'transcript-content';
        contentDiv.textContent = content;
        
        messageDiv.appendChild(header);
        messageDiv.appendChild(contentDiv);
        
        this.transcriptInner.appendChild(messageDiv);
        
        // Auto-scroll to bottom
        this.transcriptInner.scrollTop = this.transcriptInner.scrollHeight;
        
        // Limit messages to prevent overflow
        if (this.transcriptInner.children.length > 50) {
            this.transcriptInner.removeChild(this.transcriptInner.firstChild);
        }
    }
    
    saveSettings() {
        const gatewayUrl = document.getElementById('configGatewayUrl').value;
        const setupCode = document.getElementById('configSetupCode').value;
        const ttsModel = document.getElementById('configTtsModel').value;
        const referenceWav = document.getElementById('configReferenceWav').value;
        const ttsSpeaker = document.getElementById('configTtsSpeaker').value;
        const whisperModel = document.getElementById('configWhisperModel').value;
        const autoListen = document.getElementById('configAutoListen').checked;
        
        // In a real implementation, these would be sent to the server
        // For now, just update WebSocket URL if changed
        if (gatewayUrl && gatewayUrl !== this.wsUrl) {
            this.wsUrl = gatewayUrl;
            if (this.ws) {
                this.ws.close();
            }
            this.connectWebSocket();
        }
        
        console.log('Settings saved:', {
            gatewayUrl,
            setupCode,
            ttsModel,
            referenceWav,
            ttsSpeaker,
            whisperModel,
            autoListen
        });
        
        this.addTranscriptMessage('system', 'Settings saved successfully.');
    }
    
    animate() {
        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Draw orb
        this.drawOrb();
        
        // Update pulse phase
        this.pulsePhase = (this.pulsePhase + 1) % 100;
        
        // Request next frame
        requestAnimationFrame(() => this.animate());
    }
    
    drawOrb() {
        const centerX = this.canvas.width / 2;
        const centerY = this.canvas.height / 2;
        const radius = Math.min(centerX, centerY) * 0.8;
        
        // Colors based on state
        let color;
        switch(this.state) {
            case 'idle':
                color = '#00b4ff'; // Blue
                break;
            case 'wake':
                color = '#ff7700'; // Orange
                break;
            case 'listening':
                color = '#00ff88'; // Green
                break;
            case 'speaking':
                color = '#00ff88'; // Green (same as listening for now)
                break;
            case 'thinking':
                color = '#cc88ff'; // Purple
                break;
            case 'processing':
                color = '#cc88ff'; // Purple
                break;
            default:
                color = '#00b4ff';
        }
        
        // Add pulsing effect for idle state
        let alpha = 1.0;
        if (this.state === 'idle') {
            const pulse = Math.abs(50 - this.pulsePhase) / 50.0;
            alpha = 0.6 + (0.4 * pulse); // Pulse between 0.6 and 1.0
        }
        
        // Create gradient
        const gradient = this.ctx.createRadialGradient(
            centerX, centerY, 0,
            centerX, centerY, radius
        );
        
        // Convert hex to rgba
        const hexToRgba = (hex, alpha) => {
            const r = parseInt(hex.slice(1, 3), 16);
            const g = parseInt(hex.slice(3, 5), 16);
            const b = parseInt(hex.slice(5, 7), 16);
            return `rgba(${r}, ${g}, ${b}, ${alpha})`;
        };
        
        gradient.addColorStop(0, hexToRgba(color, alpha * 0.8)); // Center brighter
        gradient.addColorStop(1, hexToRgba(color, alpha * 0.2)); // Edge darker
        
        // Draw orb
        this.ctx.fillStyle = gradient;
        this.ctx.beginPath();
        this.ctx.arc(centerX, centerY, radius, 0, Math.PI * 2);
        this.ctx.fill();
        
        // Add inner glow
        this.ctx.save();
        this.ctx.globalCompositeOperation = 'lighter';
        const innerGradient = this.ctx.createRadialGradient(
            centerX, centerY, radius * 0.7,
            centerX, centerY, radius * 0.9
        );
        innerGradient.addColorStop(0, 'rgba(255, 255, 255, 0.3)');
        innerGradient.addColorStop(1, 'rgba(255, 255, 255, 0)');
        this.ctx.fillStyle = innerGradient;
        this.ctx.beginPath();
        this.ctx.arc(centerX, centerY, radius * 0.8, 0, Math.PI * 2);
        this.ctx.fill();
        this.ctx.restore();
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.jarvisOrb = new JarvisOrbUI();
});