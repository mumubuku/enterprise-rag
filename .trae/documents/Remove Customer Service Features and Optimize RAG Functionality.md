# Plan: Remove Customer Service Features and Optimize RAG Functionality

## Overview
The enterprise RAG project currently includes both RAG (Retrieval Augmented Generation) functionality and customer service features. To focus solely on RAG capabilities and optimize the system, I propose removing all customer service components and enhancing the core RAG functionality.

## Part 1: Removal of Customer Service Features

### Frontend Components to Remove
1. **CustomerService.vue** - Complete removal of the customer service workspace component
2. **Customer service API endpoints** in `frontend/src/api/index.js`:
   - Remove the entire `csAPI` object (lines 385-476)
   - Remove `csAPI` from the exported api object (line 486)

### Backend Components to Remove
1. **API Routes** in `src/api/main.py` (lines 1028-1313):
   - `@app.post("/api/v1/cs/conversations")`
   - `@app.get("/api/v1/cs/conversations")`
   - `@app.post("/api/v1/cs/conversations/{conv_id}/messages")`
   - `@app.get("/api/v1/cs/conversations/{conv_id}/messages")`
   - `@app.post("/api/v1/cs/tickets")`
   - `@app.get("/api/v1/cs/tickets")`
   - `@app.get("/api/v1/cs/tickets/{ticket_id}")`
   - `@app.post("/api/v1/cs/tickets/{ticket_id}/assign")`
   - `@app.post("/api/v1/cs/tickets/{ticket_id}/resolve")`
   - `@app.get("/api/v1/cs/tickets/{ticket_id}/comments")`
   - `@app.post("/api/v1/cs/tickets/{ticket_id}/comments")`
   - `@app.get("/api/v1/cs/statistics")`

2. **Service Files**:
   - Remove `src/services/conversation_service.py`
   - Remove `src/services/ticket_service.py`
   - Remove `src/services/intent_service.py` (if only used for customer service)
   - Remove `src/services/sentiment_service.py` (if only used for customer service)

3. **Database Models** in `src/models/database.py`:
   - Remove `Customer` class (lines 217-231)
   - Remove `CustomerOrder` class (lines 234-247)
   - Remove `Conversation` class (lines 250-268)
   - Remove `ConversationMessage` class (lines 271-281)
   - Remove `Ticket` class (lines 287-307)
   - Remove `TicketComment` class (lines 310-321)

4. **Related Imports** - Clean up imports in remaining files that referenced removed components

### Documentation Files to Update
- Update README.md to reflect the focus on RAG functionality only
- Remove any customer service related documentation in the docs/ folder

## Part 2: RAG Optimization Strategies

### Performance Optimizations
1. **Enhanced Caching**:
   - Implement Redis or in-memory caching for frequently accessed documents
   - Cache query results for similar questions
   - Add cache invalidation strategies when knowledge base updates occur

2. **Improved Retrieval Algorithms**:
   - Fine-tune the hybrid search weights (currently bm25_weight=0.3, vector_weight=0.7)
   - Optimize reranking algorithms for better relevance
   - Implement semantic caching for query embeddings

3. **Query Processing Enhancements**:
   - Add query expansion techniques to improve search accuracy
   - Implement query classification to route to appropriate knowledge bases
   - Add query reformulation capabilities

4. **System Architecture Improvements**:
   - Implement async processing for document ingestion
   - Add bulk indexing capabilities
   - Optimize vector store operations

### User Experience Improvements
1. **Enhanced Chat Interface**:
   - Improve the Chat.vue component with better UX
   - Add conversation history persistence
   - Implement better source attribution and citation

2. **Knowledge Base Management**:
   - Add advanced filtering options
   - Implement document versioning
   - Add quality scoring for retrieved documents

3. **Monitoring and Analytics**:
   - Enhance query logging with more detailed metrics
   - Add performance monitoring dashboards
   - Implement feedback collection mechanism

### Technical Optimizations
1. **Memory Management**:
   - Optimize vector store memory usage
   - Implement lazy loading for large documents
   - Add memory cleanup routines

2. **Scalability Improvements**:
   - Add support for distributed vector stores
   - Implement connection pooling
   - Add horizontal scaling capabilities

## Implementation Steps
1. Create a backup branch before making changes
2. Remove customer service components gradually
3. Test RAG functionality after each removal
4. Implement optimizations incrementally
5. Conduct performance testing
6. Update documentation

## Expected Outcomes
- Cleaner, more focused codebase dedicated to RAG functionality
- Improved performance and maintainability
- Better user experience for RAG-specific use cases
- Reduced complexity and dependencies
- Enhanced scalability for RAG operations