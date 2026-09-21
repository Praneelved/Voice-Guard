import numpy as np

class AudioRingBuffer:
    def __init__(self, max_seconds: float = 10.0, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.max_samples = int(max_seconds * sample_rate)
        self.buffer = np.zeros(self.max_samples, dtype=np.int16)
        self.current_size = 0

    def push(self, audio: np.ndarray):
        """
        Pushes new audio into the buffer.
        If it exceeds max_samples, older data is evicted.
        """
        incoming_len = len(audio)
        
        if incoming_len >= self.max_samples:
            # Incoming audio is larger than the entire buffer, just keep the tail
            self.buffer[:] = audio[-self.max_samples:]
            self.current_size = self.max_samples
            return

        # Shift existing data to the left to make room for new data
        if self.current_size + incoming_len > self.max_samples:
            overflow = (self.current_size + incoming_len) - self.max_samples
            # Shift left by overflow amount
            self.buffer[:-overflow] = self.buffer[overflow:]
            self.current_size -= overflow

        # Insert new data at the end
        self.buffer[self.current_size:self.current_size + incoming_len] = audio
        self.current_size += incoming_len

    def get_all(self) -> np.ndarray:
        """
        Returns all accumulated audio in the buffer.
        """
        return self.buffer[:self.current_size].copy()

    def get_last_seconds(self, seconds: float) -> np.ndarray:
        """
        Returns the last `seconds` of audio.
        """
        samples = int(seconds * self.sample_rate)
        if samples > self.current_size:
            return self.get_all()
        return self.buffer[self.current_size - samples:self.current_size].copy()

    def clear(self):
        self.current_size = 0
