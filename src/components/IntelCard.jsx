import VerdictBlock from './VerdictBlock'
import HeatmapBlock from './HeatmapBlock'
import ContextDrift from './ContextDrift'
import KeyInsights from './KeyInsights'
import TrustTrail from './TrustTrail'
import EmotionBar from './EmotionBar'
import HumorBlock from './HumorBlock'
import ActionButtons from './ActionButtons'

export default function IntelCard({ data, onReanalyze }) {
  if (!data) return null

  const {
    verdict,
    reality_score,
    claims,
    context_drift,
    key_insights,
    trust_trail,
    emotion_analysis,
    humor,
    sources
  } = data

  return (
    <div className="intel-card">
      <div className="intel-card__inner">
        {/* Verdict + Reality Score */}
        {verdict && (
          <VerdictBlock
            score={reality_score}
            verdict={verdict}
          />
        )}

        {/* Claim Heatmap */}
        {claims && claims.length > 0 && (
          <HeatmapBlock claims={claims} />
        )}

        {/* Context Drift Warning */}
        {context_drift && context_drift.detected && (
          <ContextDrift data={context_drift} />
        )}

        {/* Key Intelligence Insights */}
        {key_insights && key_insights.length > 0 && (
          <KeyInsights items={key_insights} />
        )}

        {/* Trust Trail */}
        {trust_trail && trust_trail.length > 0 && (
          <TrustTrail items={trust_trail} />
        )}

        {/* Emotion Analysis */}
        {emotion_analysis && emotion_analysis.intensity > 0 && (
          <EmotionBar data={emotion_analysis} />
        )}

        {/* Humor Block */}
        {humor && humor.joke && (
          <HumorBlock data={humor} />
        )}

        {/* Action Buttons */}
        <ActionButtons
          sources={sources}
          onReanalyze={onReanalyze}
        />
      </div>
    </div>
  )
}
