import streamlit as st

def render_advisor_interface():
  st.markdown(
    """
    <style>
    .advisor-container { background: var(--bg-secondary); border-radius: 8px; padding: 1.5rem; margin-bottom: 2rem; }
    .suggestion-chip { background: #2f4f7b; color: white; padding: 0.5rem; border-radius: 20px; margin: 0.3rem; display: inline-block; }
    </style>
    """,
    unsafe_allow_html=True,
  )
  with st.container():
    st.markdown(
      """
      <div class='advisor-container'>
        <h2>AI Advisor</h2>
        <div class='suggestion-section'>
          <span class='suggestion-title'>Recommendations:</span>
          <span class='suggestion-chip'>Optimize pricing strategy</span>
          <span class='suggestion-chip'>Improve customer segmentation</span>
          <span class='suggestion-chip'>Enhance supply chain efficiency</span>
        </div>
        <div class='analysis-container'>
          <h3>Market Analysis</h3>
          <p>Current market conditions indicate a 78% probability of growth in Q3.</p>
        </div>
      </div>
      """,
      unsafe_allow_html=True,
    )


def render_decision_framework():
    framework = "<div class='decision-framework'>"
    framework += "<div class='criteria-section'>"
    framework += "<h3>Decision Criteria</h3>"
    framework += "<ul class='criteria-list'>"
    framework += "<li>Financial Impact</li>"
    framework += "<li>Customer Satisfaction</li>"
    framework += "<li>Operational Efficiency</li>"
    framework += "<li>Strategic Alignment</li>"
    framework += "</ul>"
    framework += "</div>"
    framework += "<div class='recommendation-engine'>"
    framework += "<h3>Recommendation Engine</h3>"
    framework += "<div class='confidence-indicator'>Confidence: 89%</div>"
    framework += "</div>"
    framework += "</div>"
    st.markdown(framework, unsafe_allow_html=True)

if __name__ == '__main__':
    render_advisor_interface()
    render_decision_framework()