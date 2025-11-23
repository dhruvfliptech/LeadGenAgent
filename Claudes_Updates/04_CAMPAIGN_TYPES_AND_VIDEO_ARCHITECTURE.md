# Campaign Types & Video Architecture
## Flexible Campaign Modes with Cost-Optimized Video Stack
### November 4, 2025

---

## Document Purpose

Define campaign types and video architecture based on research findings and user requirements:

1. **Campaign Types** - 6 distinct campaign modes (not every email needs video)
2. **Video Stack** - Cartesia + Remotion + Bunny.net (71% cheaper than alternatives)
3. **Feature Flags** - Enable/disable components per campaign
4. **Cost Optimization** - Match campaign intensity to lead value

**Key Insight**: Not all leads need full personalization. High-value enterprise leads get video + demo; high-volume SMB leads get text-only.

---

## 1. Campaign Types Overview

### The 6 Campaign Modes

| Campaign Type | Analysis | Demo | Video | AI Copy | Cost/Lead | Use Case |
|---------------|----------|------|-------|---------|-----------|----------|
| **Full Personalized** | ✅ | ✅ | ✅ | ✅ | $0.15-0.20 | Enterprise ($100K+) |
| **Video Only** | ✅ | ❌ | ✅ | ✅ | $0.03-0.05 | Mid-market ($25K-100K) |
| **Personalized Text** | ✅ | ❌ | ❌ | ✅ | $0.005-0.01 | SMB ($5K-25K) |
| **Simple Outreach** | ❌ | ❌ | ❌ | ❌ | $0.001-0.002 | Mass campaigns |
| **Follow-Up** | ❌ | ❌ | ❌ | ✅ | $0.003-0.005 | Reply to conversations |
| **Nurture Sequence** | ❌ | ❌ | ❌ | ✅ | $0.002-0.004 | Long-term education |

---

## 2. Detailed Campaign Specifications

### 2.1 Full Personalized (Highest Touch)

**When to Use**:
- Enterprise deals ($100K+ potential)
- Strategic partnerships
- Named account targeting
- High-stakes competitive displacement

**What Gets Generated**:
1. Website analysis (AI Council insights)
2. Demo site (code generation showing improvements)
3. Video walkthrough (Cartesia voice + Remotion composition)
4. Personalized email (AI-written, references all assets)

**Email Structure**:
```
Subject: Quick improvements for [Company]'s website

Hi [FirstName],

I analyzed [Company]'s website and spotted 3 quick wins
that could boost your conversion rate 20-30%.

I built a quick demo showing what these changes could
look like: [demo_url]

And here's a 90-second walkthrough: [video_url]

Want to discuss implementation?

[Your Name]
```

**Cost Breakdown**:
- Website analysis: $0.002 (cheap model)
- Demo generation: $0.10 (code gen + deployment)
- Video generation: $0.025 (Cartesia + Remotion + hosting)
- Email generation: $0.005 (AI copy)
- **Total: $0.132/lead**

**Processing Time**: 10-15 minutes per lead

---

### 2.2 Video Only (High Touch)

**When to Use**:
- Mid-market deals ($25K-100K)
- Product demos for warm leads
- Explaining complex value propositions
- Competitive comparisons

**What Gets Generated**:
1. Website analysis (AI Council insights)
2. Video walkthrough (explaining insights, no demo build)
3. Personalized email (AI-written, video-centric)

**Email Structure**:
```
Subject: 3 ways to improve [Company]'s website

Hi [FirstName],

I recorded a quick video analyzing [Company]'s website
and sharing 3 specific improvements that could increase
conversions.

Watch here (90 seconds): [video_url]

[Include key insight #1 as preview]

Worth a conversation?

[Your Name]
```

**Cost Breakdown**:
- Website analysis: $0.002
- Video generation: $0.025
- Email generation: $0.005
- **Total: $0.032/lead**

**Processing Time**: 3-5 minutes per lead

---

### 2.3 Personalized Text (Medium Touch)

**When to Use**:
- SMB deals ($5K-25K)
- High-volume outreach (100-1000 leads/day)
- A/B testing messaging
- Testing new markets

**What Gets Generated**:
1. Website analysis (AI Council insights)
2. Personalized email (AI-written, mentions specific insights)

**Email Structure**:
```
Subject: Quick question about [Company]'s [specific feature]

Hi [FirstName],

I noticed [Company] uses [technology/approach] on your
website. Have you considered [specific improvement based
on analysis]?

We've helped [similar company] achieve [specific result]
by implementing this.

Worth exploring?

[Your Name]
```

**Cost Breakdown**:
- Website analysis: $0.002
- Email generation: $0.005
- **Total: $0.007/lead**

**Processing Time**: 30-60 seconds per lead

---

### 2.4 Simple Outreach (Low Touch, High Volume)

**When to Use**:
- Event invitations
- Content distribution (webinars, whitepapers)
- Market research surveys
- Product launch announcements
- Newsletter signups

**What Gets Generated**:
1. Template-based email with merge tags (name, company)

**Email Structure**:
```
Subject: [Event Name] - [Date]

Hi [FirstName],

We're hosting [Event Name] on [Date] and thought
[Company] might be interested.

Topics covered:
- [Topic 1]
- [Topic 2]
- [Topic 3]

Register here: [link]

See you there?

[Your Name]
```

**Cost Breakdown**:
- Template rendering: $0.001
- **Total: $0.001/lead**

**Processing Time**: 5-10 seconds per lead

---

### 2.5 Follow-Up (Conversation Continuation)

**When to Use**:
- Reply to prospect responses
- Meeting no-shows
- Post-demo follow-ups
- Proposal sent, no response

**What Gets Generated**:
1. AI-written contextual follow-up (references conversation history)

**Email Structure**:
```
Subject: Re: [Previous Subject]

Hi [FirstName],

Following up on [previous topic].

[AI-generated contextual message based on conversation]

Still interested in [specific outcome discussed]?

[Your Name]
```

**Cost Breakdown**:
- AI context analysis: $0.002
- Email generation: $0.003
- **Total: $0.005/lead**

**Processing Time**: 20-30 seconds per lead

---

### 2.6 Nurture Sequence (Long-term Education)

**When to Use**:
- Long sales cycles (6+ months)
- Educational content series
- Thought leadership positioning
- Building awareness in new markets

**What Gets Generated**:
1. Scheduled content (case studies, guides, tips)
2. AI-personalized intro based on prospect's industry/role

**Email Structure**:
```
Subject: [Educational Topic] for [Industry]

Hi [FirstName],

As someone in [Industry], you might find this relevant:

[Educational content about common challenge]

We recently helped [Similar Company] solve this by
[Approach]. Here's how: [link to case study]

Useful?

[Your Name]
```

**Cost Breakdown**:
- Industry contextualization: $0.002
- Email generation: $0.002
- **Total: $0.004/lead**

**Processing Time**: 15-20 seconds per lead

---

## 3. Video Architecture (Cartesia + Remotion + Bunny.net)

### Research Findings: 71% Cost Savings

**Alternative Considered (Replic.co)**:
- SaaS platform for AI avatar videos
- Cost: $0.10-0.50/video
- Lock-in: Proprietary, no code ownership
- **Rejected**: Too expensive, limited control

**Recommended Stack**:
- **Cartesia**: Voice synthesis (8x faster than ElevenLabs)
- **Remotion**: Programmatic video (React components)
- **Bunny.net**: CDN hosting (10x cheaper than CloudFront)
- **Total: $0.025/video** (71% cheaper than Replic.co)

---

### 3.1 Cartesia TTS (Voice Generation)

**Why Cartesia**:
- 40ms response time (vs 300ms for ElevenLabs) = **8x faster**
- Outperforms ElevenLabs in 36 of 50 blind tests
- Significantly lower pricing
- Human-level naturalness
- Real-time voice cloning

**Pricing**:
- ~$0.002 per 60-second video
- $0.10 per 1000 characters (approximate)
- Free tier available for testing

**Implementation**:
```python
from cartesia import Cartesia

client = Cartesia(api_key=settings.CARTESIA_API_KEY)

async def generate_voice(script: str, voice_id: str) -> bytes:
    """Generate natural voice from script."""

    voice_output = await client.tts.bytes(
        model_id="sonic-english",
        transcript=script,
        voice={
            "mode": "id",
            "id": voice_id  # Your cloned voice
        },
        output_format={
            "container": "wav",
            "encoding": "pcm_f32le",
            "sample_rate": 44100,
        },
    )

    return voice_output
```

**Voice Cloning** (One-Time Setup):
1. Record 2-3 minutes of your voice
2. Upload to Cartesia
3. Get voice ID for all future videos
4. Cost: Free (included in platform)

---

### 3.2 Remotion (Video Composition)

**Why Remotion**:
- React-based (familiar for developers)
- Full programmatic control (unlimited customization)
- 4K output support
- Lambda rendering (parallel, fast)
- Production-grade (used by Fortune 500)
- 17,000+ GitHub stars

**Pricing**:
- Free for individuals and small teams
- Companies: $100/month minimum ($25 per developer)
- Lambda rendering: ~$0.02-0.05 per video (depends on complexity)

**Implementation**:
```tsx
// remotion/PersonalizedVideo.tsx
import { AbsoluteFill, Sequence, Audio, Img } from 'remotion';

export const PersonalizedVideo: React.FC<{
  prospectName: string;
  companyName: string;
  websiteScreenshot: string;
  audioUrl: string;
  insights: string[];
}> = ({ prospectName, companyName, websiteScreenshot, audioUrl, insights }) => {
  return (
    <AbsoluteFill style={{ backgroundColor: '#0B132B' }}>
      {/* Audio track */}
      <Audio src={audioUrl} />

      {/* Intro with name (0-90 frames = 3 seconds at 30fps) */}
      <Sequence from={0} durationInFrames={90}>
        <AbsoluteFill style={{
          justifyContent: 'center',
          alignItems: 'center'
        }}>
          <h1 style={{ fontSize: 72, color: 'white' }}>
            Hi {prospectName}! 👋
          </h1>
        </AbsoluteFill>
      </Sequence>

      {/* Website screenshot (90-270 frames = 6 seconds) */}
      <Sequence from={90} durationInFrames={180}>
        <AbsoluteFill>
          <Img src={websiteScreenshot} style={{ width: '100%' }} />
          <div style={{
            position: 'absolute',
            bottom: 50,
            left: 50,
            color: 'white',
            background: 'rgba(0,0,0,0.7)',
            padding: 20
          }}>
            <h2>{companyName}'s Website</h2>
          </div>
        </AbsoluteFill>
      </Sequence>

      {/* Key insights (270-630 frames = 12 seconds) */}
      {insights.map((insight, i) => (
        <Sequence
          key={i}
          from={270 + (i * 120)}
          durationInFrames={120}
        >
          <AbsoluteFill style={{
            justifyContent: 'center',
            padding: 100
          }}>
            <div style={{
              background: 'rgba(108, 92, 231, 0.2)',
              padding: 40,
              borderRadius: 10
            }}>
              <h3 style={{ color: 'white', fontSize: 36 }}>
                Insight #{i + 1}
              </h3>
              <p style={{ color: 'white', fontSize: 24 }}>
                {insight}
              </p>
            </div>
          </AbsoluteFill>
        </Sequence>
      ))}

      {/* CTA (630-750 frames = 4 seconds) */}
      <Sequence from={630} durationInFrames={120}>
        <AbsoluteFill style={{
          justifyContent: 'center',
          alignItems: 'center'
        }}>
          <h2 style={{ fontSize: 48, color: 'white' }}>
            Want to discuss?
          </h2>
          <p style={{ fontSize: 32, color: '#00B894' }}>
            Book a call: [calendar_link]
          </p>
        </AbsoluteFill>
      </Sequence>
    </AbsoluteFill>
  );
};
```

**Rendering**:
```javascript
// backend/services/video_renderer.js
import { renderMediaOnLambda } from "@remotion/lambda";

async function renderVideo(leadData) {
  const { renderId, bucketName } = await renderMediaOnLambda({
    region: "us-east-1",
    functionName: "remotion-render-video",
    composition: "PersonalizedVideo",
    serveUrl: "https://your-bundle.s3.amazonaws.com",
    codec: "h264",
    inputProps: {
      prospectName: leadData.first_name,
      companyName: leadData.company_name,
      websiteScreenshot: leadData.screenshot_url,
      audioUrl: leadData.voice_url,
      insights: leadData.analysis_insights
    },
  });

  // Poll for completion
  const video = await waitForRender(renderId);

  return video.url;
}
```

---

### 3.3 Bunny.net (CDN Hosting)

**Why Bunny.net**:
- 10x cheaper than AWS CloudFront
- $0.005-0.01 per GB delivery
- $0.02/GB/month storage
- 119+ global PoPs
- Adaptive bitrate streaming
- Token authentication
- Video APIs with webhooks

**Pricing** (1000 videos/day = 30K/month):
- Storage: 30K × 100MB = 3TB × $0.02/GB = $60/month
- Delivery: 30K × 100MB × 2 views avg = 6TB × $0.01/GB = $60/month
- **Total: $120/month** (vs $1,500/month on CloudFront)

**Implementation**:
```python
# backend/services/video_uploader.py
import httpx

async def upload_to_bunny(video_path: str, video_id: str) -> str:
    """Upload video to Bunny.net CDN."""

    url = f"https://storage.bunnycdn.com/{settings.BUNNY_STORAGE_ZONE}/{video_id}.mp4"

    async with httpx.AsyncClient() as client:
        with open(video_path, 'rb') as f:
            response = await client.put(
                url,
                headers={
                    "AccessKey": settings.BUNNY_API_KEY,
                    "Content-Type": "video/mp4"
                },
                content=f
            )

    # Return CDN URL
    cdn_url = f"https://{settings.BUNNY_CDN_HOSTNAME}/{video_id}.mp4"

    return cdn_url
```

---

### 3.4 Complete Video Generation Pipeline

```python
# backend/services/video_pipeline.py
class VideoPipeline:
    """End-to-end video generation pipeline."""

    async def generate_video(
        self,
        lead: Lead,
        analysis: Dict,
        campaign: Campaign
    ) -> str:
        """Generate personalized video for lead."""

        # Step 1: Generate script
        script = await self._generate_script(lead, analysis)

        # Step 2: Generate voice (Cartesia)
        voice_url = await self._generate_voice(script, lead.id)

        # Step 3: Capture website screenshot
        screenshot_url = await self._capture_screenshot(lead.website)

        # Step 4: Prepare Remotion input
        input_props = {
            "prospectName": lead.first_name,
            "companyName": lead.company_name,
            "websiteScreenshot": screenshot_url,
            "audioUrl": voice_url,
            "insights": analysis["top_improvements"][:3]
        }

        # Step 5: Render video (Remotion Lambda)
        video_path = await self._render_video(input_props)

        # Step 6: Upload to Bunny.net
        cdn_url = await self._upload_video(video_path, lead.id)

        # Step 7: Generate thumbnail
        thumbnail_url = await self._generate_thumbnail(video_path, lead.id)

        # Step 8: Log to database
        await self._save_video_record(
            lead_id=lead.id,
            video_url=cdn_url,
            thumbnail_url=thumbnail_url,
            script=script,
            cost=0.025,
            duration_seconds=90
        )

        return cdn_url

    async def _generate_script(self, lead: Lead, analysis: Dict) -> str:
        """Generate personalized video script."""

        prompt = f"""
        Write a 90-second video script for {lead.first_name} at {lead.company_name}.

        Website analysis insights:
        {json.dumps(analysis["top_improvements"][:3], indent=2)}

        Script structure:
        - 0-10s: Greeting with name
        - 10-30s: Insight #1 (most impactful)
        - 30-50s: Insight #2
        - 50-70s: Insight #3
        - 70-90s: Soft CTA (book a call)

        Tone: Friendly, helpful, not salesy.
        Length: Exactly 200-250 words.
        """

        response = await self.ai_council.execute(
            task_type="video_script",
            prompt=prompt,
            context={"lead_id": lead.id}
        )

        return response.text

    async def _generate_voice(self, script: str, lead_id: UUID) -> str:
        """Generate voice with Cartesia."""

        voice_bytes = await self.cartesia_client.tts.bytes(
            model_id="sonic-english",
            transcript=script,
            voice={"mode": "id", "id": settings.CARTESIA_VOICE_ID},
            output_format={
                "container": "wav",
                "encoding": "pcm_f32le",
                "sample_rate": 44100
            }
        )

        # Save to temp file
        voice_path = f"/tmp/{lead_id}_voice.wav"
        with open(voice_path, 'wb') as f:
            f.write(voice_bytes)

        # Upload to S3 for Remotion access
        voice_url = await self._upload_to_s3(voice_path)

        return voice_url

    async def _render_video(self, input_props: Dict) -> str:
        """Render video with Remotion Lambda."""

        result = await renderMediaOnLambda({
            "region": "us-east-1",
            "functionName": "remotion-render",
            "composition": "PersonalizedVideo",
            "serveUrl": settings.REMOTION_BUNDLE_URL,
            "codec": "h264",
            "inputProps": input_props
        })

        # Wait for render to complete
        video_url = await self._wait_for_render(result.renderId)

        # Download from Lambda S3
        video_path = await self._download_video(video_url)

        return video_path
```

---

## 4. Cost Comparison: Video Stacks

| Component | Replic.co (SaaS) | ElevenLabs Stack | Cartesia Stack (Ours) |
|-----------|------------------|------------------|------------------------|
| **Voice** | Included | $0.03 | $0.002 |
| **Composition** | Included | Manual/FFmpeg | $0.02 (Remotion) |
| **Hosting** | Included | $0.05 (CloudFront) | $0.001 (Bunny.net) |
| **Total/Video** | **$0.10-0.50** | **$0.08** | **$0.023** |
| **30K Videos/Month** | **$3,000-15,000** | **$2,400** | **$690** |
| **Savings vs Replic** | Baseline | 84% | **95%** |

**Winner**: Cartesia + Remotion + Bunny.net = **$0.023/video**

---

## 5. Campaign Feature Flags (Database Schema)

```python
# backend/app/models/campaign.py
from enum import Enum

class CampaignType(str, Enum):
    FULL_PERSONALIZED = "full_personalized"
    VIDEO_ONLY = "video_only"
    PERSONALIZED_TEXT = "personalized_text"
    SIMPLE_OUTREACH = "simple_outreach"
    FOLLOW_UP = "follow_up"
    NURTURE_SEQUENCE = "nurture_sequence"

class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    campaign_type = Column(SQLEnum(CampaignType), nullable=False)

    # Feature flags (JSONB for flexibility)
    features = Column(JSONB, default={
        "website_analysis": False,
        "generate_demo": False,
        "generate_video": False,
        "ai_personalization": False
    })

    # Source configuration
    source_types = Column(ARRAY(String))
    filters = Column(JSONB)

    # Sending limits
    daily_limit = Column(Integer, default=100)
    send_window = Column(JSONB)  # {"start": "09:00", "end": "17:00", "timezone": "America/New_York"}

    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
```

---

## 6. Implementation Checklist

### Phase 1: Campaign Types (Week 3)
- [ ] Create CampaignType enum
- [ ] Add campaign_type column to campaigns table
- [ ] Add features JSONB column
- [ ] Build campaign creation API endpoint
- [ ] Implement feature flag logic in lead processor
- [ ] Create frontend campaign builder UI
- [ ] Add cost estimator to UI

### Phase 2: Video Stack (Week 5-6)
- [ ] Sign up for Cartesia (voice cloning)
- [ ] Clone your voice (record 2-3 minutes)
- [ ] Set up Remotion project
- [ ] Create PersonalizedVideo React component
- [ ] Deploy Remotion Lambda function
- [ ] Set up Bunny.net CDN account
- [ ] Build video pipeline service
- [ ] Integrate with campaign processor
- [ ] Test end-to-end video generation
- [ ] Monitor costs and quality

### Phase 3: Testing & Optimization (Week 7)
- [ ] A/B test video vs text campaigns
- [ ] Track reply rates by campaign type
- [ ] Optimize video scripts based on engagement
- [ ] Fine-tune Remotion composition timing
- [ ] Verify Bunny.net CDN performance globally

---

## 7. Success Metrics by Campaign Type

| Campaign Type | Target Reply Rate | Target Meeting Rate | Cost/Meeting |
|---------------|-------------------|---------------------|--------------|
| **Full Personalized** | 15-25% | 5-10% | $1.50-4.00 |
| **Video Only** | 10-15% | 3-5% | $0.60-1.67 |
| **Personalized Text** | 5-10% | 1-3% | $0.10-1.00 |
| **Simple Outreach** | 1-3% | 0.5-1% | $0.10-0.40 |
| **Follow-Up** | 20-30% | 10-15% | $0.03-0.05 |
| **Nurture Sequence** | 3-5% | 1-2% | $0.08-0.40 |

---

## 8. Key Takeaways

### Campaign Flexibility
✅ **6 campaign types** - Match intensity to lead value
✅ **Feature flags** - Enable/disable components per campaign
✅ **Cost transparency** - Estimate before launching
✅ **A/B testing** - Compare approaches with data

### Video Architecture
✅ **71% cost savings** - $0.023/video vs $0.08+ alternatives
✅ **8x faster TTS** - Cartesia outperforms ElevenLabs
✅ **Full control** - React components = unlimited customization
✅ **Production-ready** - Used by Fortune 500 companies

### Smart Routing
✅ **Enterprise** → Full Personalized ($0.15/lead)
✅ **Mid-market** → Video Only ($0.03/lead)
✅ **SMB** → Personalized Text ($0.007/lead)
✅ **Mass** → Simple Outreach ($0.001/lead)

---

**Document Owner**: Product + Engineering
**Last Updated**: November 4, 2025
**Status**: Implementation Ready
**Related Docs**:
- `01_ENHANCED_SOFTWARE_ARCHITECTURE.md` (system design)
- `03_COST_OPTIMIZATION_GUIDE.md` (cost strategies)
- `05_MVP_QUICK_START_GUIDE.md` (implementation guide)
