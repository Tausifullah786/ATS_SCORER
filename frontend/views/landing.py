import streamlit as st


def render():
    
    # Hero Section
    st.markdown("""
    <div class="main-header">
        <div class="hero-copy">
            <span class="hero-eyebrow">MAKE YOUR NEXT MOVE COUNT</span>
            <h1>ATS Resume Scorer</h1>
            <h3>Optimize Your Resume for Applicant Tracking Systems</h3>
            <p>Get instant feedback on your resume's ATS compatibility with AI-powered analysis</p>
            <div class="hero-tags"><span>Resume scoring</span><span>Skill validation</span><span>Job matching</span></div>
        </div>
        <div class="resume-art" aria-hidden="true">
            <div class="resume-sheet">
                <span class="doc-heading"></span><span class="doc-subheading"></span>
                <span class="doc-section"></span>
                <span class="doc-line"></span><span class="doc-line"></span><span class="doc-line short"></span>
                <span class="doc-section"></span>
                <span class="doc-line"></span><span class="doc-line short"></span><span class="doc-line"></span>
                <span class="doc-section"></span>
                <span class="doc-line"></span><span class="doc-line short"></span>
                <span class="doc-check">✓</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Call-to-Action Button
    col1, col2, col3 = st.container(key="home_cta").columns([1, 2, 1])
    with col2:
        if st.button("🚀 Start Analyzing Your Resume", use_container_width=True, type="primary"):
            st.session_state.current_view = 'scorer'
            st.rerun()
    
    st.markdown("---")
    
    # Features Overview
    st.markdown("## ✨ Key Features")
    
    col1, col2, col3 = st.container(key="home_features").columns(3, gap="medium")
    
    with col1:
        st.markdown('<div class="feature-number">01 / UNDERSTAND YOUR SCORE</div>', unsafe_allow_html=True)
        st.markdown("""
        ### 📊 Comprehensive Scoring
        Get detailed scores across 5 key dimensions:
        - Formatting (20%)
        - Keywords & Skills (25%)
        - Content Quality (25%)
        - Skill Validation (15%)
        - ATS Compatibility (15%)
        """)
    
    with col2:
        st.markdown('<div class="feature-number">02 / SHOW YOUR STRENGTHS</div>', unsafe_allow_html=True)
        st.markdown("""
        ### 🔍 Skill Validation
        Verify that your claimed skills are demonstrated in your projects and experience using AI-powered semantic analysis.
        
        **No more empty claims!**
        """)
    
    with col3:
        st.markdown('<div class="feature-number">03 / YOUR WORKSPACE</div>', unsafe_allow_html=True)
        st.markdown("""
        ### 🔒 Privacy First
        All analysis runs locally with no external API calls. Your resume data never leaves your system.
        
        **100% Private & Secure**
        """)
    
    st.markdown("---")
    
    # How It Works
    st.markdown("## 🚀 How It Works")
    
    col1, col2, col3 = st.container(key="home_steps").columns(3, gap="medium")
    
    with col1:
        st.markdown("""
        #### 01 · Upload Your Resume
        Support for PDF, DOC, and DOCX formats
        """)
    
    with col2:
        st.markdown("""
        #### 02 · AI Analysis
        Our local AI models analyze your resume across multiple dimensions
        """)
    
    with col3:
        st.markdown("""
        #### 03 · Get Actionable Feedback
        Receive detailed recommendations to improve your resume
        """)
