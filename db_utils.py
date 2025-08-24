from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from typing import List, Dict, Any, Optional
import json
from config import Config

Base = declarative_base()

class ProcessedDocument(Base):
    __tablename__ = 'processed_documents'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_type = Column(String(10), nullable=False)
    file_size = Column(Integer)  # Size in bytes
    
    # OCR Results
    extracted_text = Column(Text)
    
    # AI Processing Results
    document_type = Column(String(50))
    confidence_score = Column(Float)
    extracted_fields = Column(Text)  # Store as JSON string for MySQL compatibility
    summary = Column(Text)
    document_metadata = Column(Text)  # Store additional metadata as JSON string
    
    # Storage Information
    github_url = Column(String(500))  # URL to original file in GitHub
    
    # Timestamps
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)
    
    # Tags
    tags = Column(String(255))  # Comma-separated tags
    
    def to_dict(self):
        """Convert document to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'extracted_text': self.extracted_text,
            'document_type': self.document_type,
            'confidence_score': self.confidence_score,
            'extracted_fields': json.loads(self.extracted_fields) if self.extracted_fields else {},
            'summary': self.summary,
            'document_metadata': json.loads(self.document_metadata) if self.document_metadata else {},
            'github_url': self.github_url,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'tags': self.tags,
        }

class AuditLog(Base):
    __tablename__ = 'audit_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer)
    action = Column(String(50))
    user = Column(String(100))
    timestamp = Column(DateTime, default=datetime.utcnow)
    summary = Column(Text)

class DatabaseManager:
    def __init__(self):
        self.config = Config()
        self.engine = create_engine(self.config.DB_URL, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create tables if they don't exist
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()
    
    def create_document(self, 
                       filename: str,
                       original_filename: str, 
                       file_type: str,
                       file_size: int,
                       extracted_text: str,
                       ai_results: Dict[str, Any],
                       github_url: str,
                       tags: str = "") -> ProcessedDocument:
        """Create a new processed document record"""
        
        session = self.get_session()
        try:
            doc = ProcessedDocument(
                filename=filename,
                original_filename=original_filename,
                file_type=file_type,
                file_size=file_size,
                extracted_text=extracted_text,
                document_type=ai_results.get('document_type'),
                confidence_score=ai_results.get('confidence_score'),
                extracted_fields=json.dumps(ai_results.get('extracted_fields', {})),
                summary=ai_results.get('summary'),
                document_metadata=json.dumps(ai_results.get('metadata', {})),
                github_url=github_url,
                processed_at=datetime.utcnow(),
                tags=tags
            )
            
            session.add(doc)
            session.commit()
            session.refresh(doc)
            return doc
        
        finally:
            session.close()
    
    def get_document_by_id(self, doc_id: int) -> Optional[ProcessedDocument]:
        """Get document by ID"""
        session = self.get_session()
        try:
            return session.query(ProcessedDocument).filter(ProcessedDocument.id == doc_id).first()
        finally:
            session.close()
    
    def get_all_documents(self, limit: int = 100, offset: int = 0) -> List[ProcessedDocument]:
        """Get all documents with pagination"""
        session = self.get_session()
        try:
            return session.query(ProcessedDocument)\
                         .order_by(ProcessedDocument.uploaded_at.desc())\
                         .limit(limit)\
                         .offset(offset)\
                         .all()
        finally:
            session.close()
    
    def search_documents(self, 
                        search_query: str = None,
                        document_type: str = None,
                        date_from: datetime = None,
                        date_to: datetime = None,
                        tag_query: str = None,
                        limit: int = 100) -> List[ProcessedDocument]:
        """Search documents with various filters, including tag-based search"""
        session = self.get_session()
        try:
            query = session.query(ProcessedDocument)

            if search_query:
                query = query.filter(
                    (ProcessedDocument.extracted_text.contains(search_query)) |
                    (ProcessedDocument.summary.contains(search_query)) |
                    (ProcessedDocument.original_filename.contains(search_query))
                )

            if document_type and document_type != 'all':
                query = query.filter(ProcessedDocument.document_type == document_type)

            if date_from:
                query = query.filter(ProcessedDocument.uploaded_at >= date_from)

            if date_to:
                query = query.filter(ProcessedDocument.uploaded_at <= date_to)


            return query.order_by(ProcessedDocument.uploaded_at.desc()).limit(limit).all()

        finally:
            session.close()
    
    def get_document_types(self) -> List[str]:
        """Get all unique document types in the database"""
        session = self.get_session()
        try:
            types = session.query(ProcessedDocument.document_type)\
                          .distinct()\
                          .filter(ProcessedDocument.document_type.isnot(None))\
                          .all()
            return [t[0] for t in types]
        finally:
            session.close()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        session = self.get_session()
        try:
            total_docs = session.query(ProcessedDocument).count()
            
            type_counts = {}
            from sqlalchemy import func
            types = session.query(ProcessedDocument.document_type, func.count(ProcessedDocument.id))\
                         .group_by(ProcessedDocument.document_type)\
                         .all()
            for doc_type, count in types:
                if doc_type:
                    type_counts[doc_type] = count
            
            # Get recent activity (last 7 days)
            from datetime import timedelta
            week_ago = datetime.utcnow() - timedelta(days=7)
            recent_count = session.query(ProcessedDocument)\
                                 .filter(ProcessedDocument.uploaded_at >= week_ago)\
                                 .count()
            
            return {
                'total_documents': total_docs,
                'document_types': type_counts,
                'recent_uploads': recent_count
            }
        finally:
            session.close()
    
    def delete_document(self, doc_id: int) -> bool:
        """Delete a document by ID"""
        session = self.get_session()
        try:
            doc = session.query(ProcessedDocument).filter(ProcessedDocument.id == doc_id).first()
            if doc:
                session.delete(doc)
                session.commit()
                return True
            return False
        finally:
            session.close()
    
    def log_action(self, document_id: int, action: str, user: str, summary: str = ""):
        session = self.get_session()
        try:
            log = AuditLog(
                document_id=document_id,
                action=action,
                user=user,
                summary=summary
            )
            session.add(log)
            session.commit()
        finally:
            session.close()

    def get_audit_logs(self, document_id: int) -> list:
        session = self.get_session()
        try:
            return session.query(AuditLog).filter(AuditLog.document_id == document_id).order_by(AuditLog.timestamp.desc()).all()
        finally:
            session.close()

    def get_audit_logs_for_all(self) -> list:
        session = self.get_session()
        try:
            return session.query(AuditLog).order_by(AuditLog.timestamp.desc()).all()
        finally:
            session.close()

def get_db_manager():
    """Factory function to get database manager instance"""
    return DatabaseManager()
