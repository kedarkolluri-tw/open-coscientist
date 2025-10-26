# UI Improvement Plan: Real-Time Research Visibility

## Problem Statement
The current Coscientist UI provides **zero visibility** into the research process during execution. Users cannot:
- See which stage the system is in
- Monitor progress through the 20-iteration limit
- View intermediate results as they're generated
- Understand what's happening when the system gets stuck
- Estimate time remaining or completion status

This leads to failed research runs with no debugging capability.

---

## High-Level Plan

### Phase 1: Foundation (Core Infrastructure)
**Goal**: Establish real-time communication between backend and frontend

**Key Components**:
1. **Progress State Management**: Extend `CoscientistStateManager` to track real-time progress
2. **WebSocket/SSE Integration**: Enable live updates to Streamlit UI
3. **Progress API**: Create endpoints for current status, stage, and intermediate results
4. **State Persistence**: Save progress updates to enable resume from any point

### Phase 2: Real-Time Monitoring (Live Dashboard)
**Goal**: Provide comprehensive live visibility into research execution

**Key Components**:
1. **Live Progress Dashboard**: Real-time iteration counter, stage indicator, current action
2. **Intermediate Results Display**: Show hypotheses, tournament rankings as they're generated
3. **Stage-Based Progress Bars**: Visual progress through Early/Mid/Late stages
4. **Action History**: Live feed of supervisor decisions and reasoning

### Phase 3: Enhanced User Experience (Advanced Features)
**Goal**: Provide professional-grade monitoring and control capabilities

**Key Components**:
1. **ETA Estimation**: Time remaining based on historical data
2. **Performance Metrics**: Real-time statistics (hypothesis quality, diversity scores)
3. **Interactive Controls**: Pause/resume, manual intervention options
4. **Alert System**: Notifications for errors, completion, or stuck states

---

## Low-Level Implementation Plan

### 1. Progress State Management

#### 1.1 Extend CoscientistStateManager
```python
class ProgressState:
    current_iteration: int
    max_iterations: int
    current_stage: str  # "Early", "Mid", "Late"
    current_action: str
    action_start_time: datetime
    estimated_completion: datetime
    intermediate_results: dict
    performance_metrics: dict

class CoscientistStateManager:
    def __init__(self, state: CoscientistState):
        self.progress = ProgressState()
        self.progress_callbacks = []
    
    def update_progress(self, **kwargs):
        # Update progress state
        # Trigger callbacks for UI updates
        # Save to persistent storage
```

#### 1.2 Progress Tracking Integration
- **Framework Integration**: Modify `CoscientistFramework.run()` to emit progress updates
- **Agent Integration**: Add progress callbacks to each agent execution
- **State Persistence**: Save progress updates alongside checkpoints

### 2. Real-Time Communication

#### 2.1 WebSocket/SSE Setup
```python
# Streamlit WebSocket integration
class ProgressWebSocket:
    def __init__(self):
        self.connections = []
    
    def broadcast_progress(self, progress_data):
        # Send to all connected clients
    
    def register_callback(self, callback):
        # Register UI update callbacks
```

#### 2.2 Progress API Endpoints
```python
@app.get("/api/progress/{goal_id}")
async def get_current_progress(goal_id: str):
    # Return current progress state
    
@app.get("/api/intermediate-results/{goal_id}")
async def get_intermediate_results(goal_id: str):
    # Return latest hypotheses, rankings, etc.
```

### 3. Live Dashboard Components

#### 3.1 Progress Header Component
```python
def render_progress_header(progress_state):
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Iteration", f"{progress_state.current_iteration}/{progress_state.max_iterations}")
    
    with col2:
        st.metric("Stage", progress_state.current_stage)
    
    with col3:
        st.metric("Current Action", progress_state.current_action)
    
    with col4:
        st.metric("ETA", progress_state.estimated_completion)
```

#### 3.2 Progress Bar Component
```python
def render_progress_bar(progress_state):
    # Overall progress (iterations)
    overall_progress = progress_state.current_iteration / progress_state.max_iterations
    st.progress(overall_progress)
    
    # Stage-based progress
    stage_progress = calculate_stage_progress(progress_state)
    st.progress(stage_progress, label=f"Stage Progress: {progress_state.current_stage}")
```

#### 3.3 Live Results Component
```python
def render_live_results(progress_state):
    # Live hypothesis feed
    st.subheader("Live Hypothesis Generation")
    for hypothesis in progress_state.intermediate_results.get("hypotheses", []):
        st.write(f"✅ {hypothesis.hypothesis[:100]}...")
    
    # Live tournament rankings
    st.subheader("Live Tournament Rankings")
    for ranking in progress_state.intermediate_results.get("rankings", []):
        st.write(f"🏆 {ranking.hypothesis_id}: {ranking.elo_rating}")
```

### 4. Enhanced Monitoring Features

#### 4.1 Performance Metrics Dashboard
```python
def render_performance_metrics(progress_state):
    metrics = progress_state.performance_metrics
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Hypothesis Quality", f"{metrics.avg_elo:.0f}")
    
    with col2:
        st.metric("Diversity Score", f"{metrics.diversity_score:.2f}")
    
    with col3:
        st.metric("Success Rate", f"{metrics.success_rate:.1%}")
```

#### 4.2 Action History Feed
```python
def render_action_history(progress_state):
    st.subheader("Live Action Feed")
    
    for action in progress_state.action_history:
        timestamp = action.timestamp
        action_type = action.action
        reasoning = action.reasoning
        
        st.write(f"🕐 {timestamp}: {action_type}")
        with st.expander("Reasoning"):
            st.write(reasoning)
```

### 5. Error Handling and Recovery

#### 5.1 Error State Management
```python
class ErrorState:
    error_type: str
    error_message: str
    error_timestamp: datetime
    recovery_suggestions: list[str]
    can_retry: bool
```

#### 5.2 Stuck State Detection
```python
def detect_stuck_state(progress_state):
    # Detect if system is stuck
    # - Same action repeated too many times
    # - No progress for extended period
    # - Error rate too high
    
    if is_stuck:
        return ErrorState(
            error_type="stuck",
            error_message="System appears to be stuck",
            recovery_suggestions=["Restart", "Change parameters", "Manual intervention"]
        )
```

---

## Implementation Timeline

### Week 1: Foundation
- [ ] Extend `CoscientistStateManager` with progress tracking
- [ ] Implement progress state persistence
- [ ] Create basic progress API endpoints
- [ ] Set up WebSocket/SSE infrastructure

### Week 2: Live Dashboard
- [ ] Build progress header component
- [ ] Implement progress bars and stage indicators
- [ ] Create live results display
- [ ] Add action history feed

### Week 3: Enhanced Features
- [ ] Implement performance metrics dashboard
- [ ] Add ETA estimation
- [ ] Create error handling and recovery
- [ ] Add stuck state detection

### Week 4: Polish and Testing
- [ ] UI/UX polish and responsive design
- [ ] Performance optimization
- [ ] Comprehensive testing
- [ ] Documentation and user guides

---

## Success Metrics

### Quantitative Metrics
- **Visibility**: 100% of research stages visible in real-time
- **Debugging**: Ability to identify failure points within 5 minutes
- **User Satisfaction**: Clear progress indication throughout execution
- **Recovery**: Ability to resume from any point in the process

### Qualitative Metrics
- **User Confidence**: Users understand what's happening
- **Debugging Capability**: Easy identification of issues
- **Professional Feel**: Enterprise-grade monitoring experience
- **Reliability**: System doesn't get stuck without detection

---

## Technical Considerations

### Performance
- **Minimal Overhead**: Progress tracking should not slow down research
- **Efficient Updates**: Only send changed data to UI
- **Scalable**: Support multiple concurrent research sessions

### Reliability
- **Fault Tolerance**: Progress tracking should not break research
- **Data Consistency**: Progress state should always be accurate
- **Recovery**: System should recover from progress tracking failures

### User Experience
- **Responsive**: UI should update smoothly and quickly
- **Intuitive**: Progress indicators should be self-explanatory
- **Comprehensive**: All important information should be visible
- **Actionable**: Users should be able to take action based on progress

---

## Next Steps

1. **Review and Approve Plan**: Get stakeholder approval for the approach
2. **Start with Foundation**: Begin with progress state management
3. **Iterative Development**: Build and test each component incrementally
4. **User Feedback**: Get feedback on each phase before proceeding
5. **Documentation**: Document all new components and APIs

This plan transforms the Coscientist UI from a "black box" into a transparent, monitorable, and debuggable research system.
