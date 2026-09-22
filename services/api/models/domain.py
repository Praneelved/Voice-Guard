from sqlalchemy import Column, String, Float, Integer, Boolean, ForeignKey, DateTime, JSON, Text, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from .base import Base, TimestampMixin

class Organization(Base, TimestampMixin):
    __tablename__ = "organizations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)

class User(Base, TimestampMixin):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False)
    role = Column(String(50), nullable=False, default="viewer")
    
    organization = relationship("Organization")

class UserDevice(Base, TimestampMixin):
    __tablename__ = "user_devices"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    push_token = Column(String(255), nullable=False, unique=True)
    platform = Column(String(50), nullable=True)
    enabled = Column(Boolean, nullable=False, default=True)
    last_seen_at = Column(DateTime(timezone=True), nullable=False)
    
    user = relationship("User")

class ProtectedNumber(Base, TimestampMixin):
    __tablename__ = "protected_numbers"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    provider = Column(String(50), nullable=False) # e.g. "twilio"
    provider_number = Column(String(50), nullable=False, index=True) # e.g. "+1234567890"
    enabled = Column(Boolean, nullable=False, default=True)
    
    user = relationship("User")

class CallSession(Base, TimestampMixin):
    __tablename__ = "call_sessions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    provider_call_id = Column(String(255), nullable=False, index=True) # Twilio CallSid
    
    started_at = Column(DateTime(timezone=True), nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    
    max_risk_level = Column(String(50), nullable=False, default="STARTING")
    final_risk_score = Column(Float, nullable=True)
    
    total_windows = Column(Integer, nullable=False, default=0)
    analyzed_windows = Column(Integer, nullable=False, default=0)
    
    organization = relationship("Organization")

class RiskEvent(Base):
    __tablename__ = "risk_events"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    call_id = Column(UUID(as_uuid=True), ForeignKey("call_sessions.id"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    
    risk_level = Column(String(50), nullable=False)
    risk_score = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    
    call = relationship("CallSession")

class SignalScore(Base):
    __tablename__ = "signal_scores"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    call_id = Column(UUID(as_uuid=True), ForeignKey("call_sessions.id"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    
    antispoof_score = Column(Float, nullable=True)
    audio_quality = Column(String(50), nullable=True)
    speech_duration = Column(Float, nullable=True)
    
    call = relationship("CallSession")

class Alert(Base, TimestampMixin):
    __tablename__ = "alerts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    call_id = Column(UUID(as_uuid=True), ForeignKey("call_sessions.id"), nullable=False, index=True)
    
    alert_type = Column(String(100), nullable=False) # e.g. "spoof_detected"
    severity = Column(String(50), nullable=False, index=True) # e.g. "HIGH", "CRITICAL"
    status = Column(String(50), nullable=False, default="active") # "active", "resolved"
    
    call = relationship("CallSession")
    organization = relationship("Organization")

class SpeakerProfile(Base, TimestampMixin):
    __tablename__ = "speaker_profiles"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    embedding_path = Column(Text, nullable=False)
    
    user = relationship("User")

class TrustedVoice(Base, TimestampMixin):
    __tablename__ = "trusted_voices"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    label = Column(String(100), nullable=True) # e.g. 'CEO', 'Manager'
    
    user = relationship("User")
    embeddings = relationship("VoiceEmbedding", back_populates="trusted_voice", cascade="all, delete-orphan")

class VoiceEmbedding(Base, TimestampMixin):
    __tablename__ = "voice_embeddings"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trusted_voice_id = Column(UUID(as_uuid=True), ForeignKey("trusted_voices.id"), nullable=False, index=True)
    
    embedding = Column(ARRAY(Float), nullable=False)
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(50), nullable=False)
    
    trusted_voice = relationship("TrustedVoice", back_populates="embeddings")

class VerificationAction(Base, TimestampMixin):
    __tablename__ = "verification_actions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    call_id = Column(UUID(as_uuid=True), ForeignKey("call_sessions.id"), nullable=False, index=True)
    action_type = Column(String(100), nullable=False) # "push_notification", "sms", "knowledge_query"
    status = Column(String(50), nullable=False) # "pending", "success", "failed"
    
    call = relationship("CallSession")

class ModelVersion(Base, TimestampMixin):
    __tablename__ = "model_versions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_name = Column(String(255), nullable=False)
    version = Column(String(100), nullable=False)
    deployed_at = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, nullable=False, default=False)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    action = Column(String(255), nullable=False)
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(String(255), nullable=True)
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False)
