import { useState, useRef, useEffect } from "react";

const GLOBAL_CSS = `
@keyframes er-spin{to{transform:rotate(360deg)}}
@keyframes er-pulse{0%,100%{opacity:.5}50%{opacity:1}}
@keyframes er-bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-6px)}}
@keyframes er-gflash{0%{opacity:0;transform:translate(-50%,-50%) scale(.8)}20%{opacity:.6;transform:translate(-50%,-50%) scale(1)}100%{opacity:0;transform:translate(-50%,-60%) scale(1)}}
`;

const LENSES = [
  { n:"The Comedian", e:"😂", color:"#ff6b9d", bg:"rgba(255,107,157,0.15)" },
  { n:"The Stoic", e:"🏛", color:"#c9a84c", bg:"rgba(201,168,76,0.15)" },
  { n:"The Nihilist", e:"🕳", color:"#8a8690", bg:"rgba(255,255,255,0.06)" },
  { n:"The Optimist", e:"☀️", color:"#3ecf8e", bg:"rgba(62,207,142,0.15)" },
  { n:"The Pessimist", e:"⛈", color:"#ff4757", bg:"rgba(255,71,87,0.15)" },
  { n:"Your Best Friend", e:"🫂", color:"#4a7cff", bg:"rgba(74,124,255,0.15)" },
  { n:"The Poet", e:"🪶", color:"#9b6dff", bg:"rgba(155,109,255,0.15)" },
  { n:"A Five-Year-Old", e:"🧸", color:"#f0c832", bg:"rgba(255,200,50,0.15)" },
  { n:"The CEO", e:"📊", color:"#f0ece4", bg:"rgba(240,236,228,0.08)" },
  { n:"The Therapist", e:"🪷", color:"#00d4aa", bg:"rgba(0,212,170,0.15)" },
  { n:"Your Grandma", e:"🍪", color:"#e8653a", bg:"rgba(232,101,58,0.15)" },
  { n:"The Alien", e:"👽", color:"#4affb4", bg:"rgba(74,255,180,0.12)" },
  { n:"The Historian", e:"📜", color:"#d4a843", bg:"rgba(201,168,76,0.12)" },
  { n:"The Philosopher", e:"🦉", color:"#b08aff", bg:"rgba(155,109,255,0.12)" },
  { n:"Future You", e:"⏳", color:"#6e9fff", bg:"rgba(74,124,255,0.12)" },
  { n:"Drill Sergeant", e:"🎖", color:"#c8c0b4", bg:"rgba(240,236,228,0.1)" },
  { n:"The Monk", e:"🧘", color:"#40dfb0", bg:"rgba(0,212,170,0.1)" },
  { n:"The Scientist", e:"🔬", color:"#5a8cff", bg:"rgba(74,124,255,0.12)" },
  { n:"Conspiracy Theorist", e:"🔺", color:"#e8b830", bg:"rgba(255,200,50,0.12)" },
  { n:"Your Dog", e:"🐕", color:"#f0a070", bg:"rgba(232,101,58,0.12)" },
];

const TAKES = [
  { head:"You invented a time machine but it only goes to your inbox", body:"Look, we've all sent an email we regret. You're not special \u2014 you're just the latest member of the world's largest support group. The recruiter has probably already filed your message under 'People Having A Day' and moved on to the forty other candidates who ALSO bombed and just didn't have the artistic flair to follow up with a spicy email. Think about it: in the grand taxonomy of post-interview meltdowns, a passive-aggressive email is honestly mid-tier. You didn't show up at their office with a PowerPoint about why they're wrong. You didn't start a LinkedIn thread. You sent a slightly salty email \u2014 that's basically a Tuesday in recruiting." },
  { head:"The arrow has left the bow \u2014 attend now to your character", body:"What is done cannot be undone, and to wish otherwise is to wage war against reality itself. The interview has passed. The email has been sent. These events now belong to the universe, not to you. What remains in your power is this: how you choose to regard your own error, and what kind of person you become in its aftermath. You feel shame \u2014 good. Shame is the teacher of the virtuous, for it means your character recognized a deviation from its own standards. But to dwell endlessly in that shame is to commit a second error: squandering the present moment on what the past has already consumed. Write a brief, honest apology if you must, then release this burden. The obstacle is not the email \u2014 it is your refusal to set it down." },
  { head:"Nobody will remember this at your funeral", body:"Here's what's actually happening: you sent a mildly rude email to a stranger who processes hundreds of candidates a month and whose entire memory of you will dissolve within a fiscal quarter. The company will not erect a plaque. There is no permanent record in the Book of Professional Embarrassments. The recruiter is a temporary arrangement of atoms who will one day return to stardust, just like you, just like that email server. And isn't that weirdly beautiful? The total cosmic insignificance of this moment means you are completely, radically free to just... move on. The universe didn't notice your email. It's too busy expanding." },
  { head:"This regret is proof you're growing in real time", body:"Stay with me here: the fact that you recognize the email was wrong means your self-awareness is leagues ahead of most people. You didn't double down. You didn't convince yourself you were justified. You immediately saw the gap between who you acted like and who you actually are \u2014 that's emotional intelligence in action. And honestly? A bad interview followed by regrettable behavior is one of the most powerful forcing functions for growth. This is the moment you develop the professional resilience that will carry you through the next twenty years. The job you actually land \u2014 the one that's coming \u2014 will be one where you walk in as the person who learned from this, not the person who never had to." },
  { head:"Yes the email was bad \u2014 now let's defuse the actual damage", body:"Let's look at the worst case honestly. The recruiter reads your email, thinks poorly of you, flags you in their system, and you never work with that company again. Maybe they mention it to a colleague. That's it. That's the absolute floor. You don't get blacklisted from your entire industry over one testy email \u2014 recruiting is too high-volume and too transactional for that. The recruiter has seen worse this week, guaranteed. Now here's what's actually hurting you: not the email itself, but the rumination loop. The damage was a 3 out of 10. Your brain is treating it like an 11. You've survived every professional embarrassment you've ever had. Your track record of getting through awkward moments is literally perfect." },
  { head:"Babe you need to put the phone down and breathe", body:"Okay first of all \u2014 you're spiraling and I love you but you need to stop refreshing that sent folder. Yes, the email was a bad call. We both know that. But you know what? You were frustrated and hurt and you reacted like a human being, not a LinkedIn robot. The recruiter is not sitting at home right now drafting a manifesto about you. They've moved on. You know what you should do? Send a short 'hey, I reflected on my earlier message and I apologize for the tone' email if it'll help you sleep. Then close the laptop. Seriously. This is not your villain origin story \u2014 it's a Tuesday you'll barely remember by summer." },
  { head:"Even regret is a form of reaching toward who you want to be", body:"There is a particular kind of ache that comes from watching yourself become someone you didn't intend \u2014 the moment the send button clicked and you felt the word leave you like a stone that cannot be uncalled from the well. But consider: only someone who cares deeply about integrity could feel this wound so sharply. Your regret is not your enemy. It is the compass needle swinging back to true north, proof that your moral center holds even when your worst impulse briefly takes the wheel. The email is a sentence in a very long story, and you are already writing the next chapter simply by feeling what you feel right now." },
  { head:"Wait so you were mean to someone and now you feel bad?", body:"That happens to me too sometimes like when I pushed Tyler at recess and then I felt really really bad in my tummy. My teacher says when you do something mean you should say sorry and then it's okay again. Did you say sorry? You should say sorry. Also why did the interview go bad, did you forget to practice? I practice my ABCs before tests and it helps. Also maybe you should have a juice box because sometimes when I'm upset it's actually because I'm just thirsty and then I drink juice and everything is fine again." },
  { head:"You're over-investing emotional capital in a sunk cost", body:"Let's run the numbers on your current resource allocation. You're spending approximately 100% of your cognitive bandwidth on an event with zero remaining ROI. The interview is a sunk cost \u2014 irrecoverable regardless of rumination volume. The email represents a minor reputational liability with one stakeholder in a market containing thousands of potential employers. Your opportunity cost right now is staggering: every hour spent replaying this scenario is an hour not spent optimizing your next pitch, expanding your pipeline, or refining your interview methodology. I'd recommend a brief damage-control communication to neutralize the email liability, then a full portfolio rebalance toward forward-looking opportunities. The market doesn't reward backward-looking analysis of failed deals." },
  { head:"I'm noticing a pattern of all-or-nothing thinking here", body:"What I'm hearing is that you're experiencing intense shame, and your mind is doing something very common \u2014 it's taking a single event and globalizing it into a statement about who you are as a person. 'I sent a bad email' has become 'I am the kind of person who does this.' That's a cognitive distortion called labeling. I'd also gently point out that the interview going badly likely activated a vulnerability \u2014 perhaps around competence or being judged \u2014 and the email was an attempt to regain a sense of control or dignity. That's very human. The rumination you're experiencing now is your brain trying to 'solve' something that can't be solved by thinking about it more. What would it feel like to acknowledge the mistake without making it mean something permanent about you?" },
  { head:"Oh honey, sit down, I'll make you some tea", body:"Sweetheart, let me tell you something. Your grandfather once told his boss to go to hell in 1974 and then had to go back to work Monday morning and pretend nothing happened. He worked there another twelve years. People forget, darling, they really do. You sent a grumpy email \u2014 you didn't burn down a building. Now I want you to do three things for me: eat a proper meal, not that snacking nonsense. Get some sleep \u2014 real sleep, not lying there staring at the ceiling playing it all back. And tomorrow morning you send a nice short apology note. That's it. That's the whole plan. The world keeps spinning, my love." },
  { head:"Subject has entered recursive shame loop \u2014 fascinating specimen behavior", body:"Field notes, cycle 4,271: The human performed a ritualized competency display ('interview') before a resource gatekeeper and received negative social feedback. Rather than simply seeking an alternative resource node \u2014 their colony has thousands \u2014 the subject then transmitted a dominance-assertion signal ('passive-aggressive email') through their electronic communication web, immediately triggering their species' extraordinarily powerful regret circuitry. Most puzzling: the subject is now allocating maximum cognitive resources to replaying an event that cannot be altered, a behavior we have classified as 'temporal fixation syndrome.' The human brain appears to lack a basic cache-clearing function. We recommend further observation but note that this specimen's capacity for self-reflection suggests above-average developmental potential." },
  { head:"History's greatest comebacks started with worse emails than yours", body:"In 1838, a young politician named Abraham Lincoln wrote an anonymous letter to a newspaper savagely mocking a political rival. When discovered, he was challenged to a duel and came within inches of destroying his career and his life over a moment of petty written rage. He learned from it profoundly, becoming legendary for his restraint and grace under pressure. Winston Churchill was fired from the Admiralty after the Gallipoli disaster \u2014 his response was far more intemperate than your email, and yet history bent back toward him. The pattern is remarkably consistent: a moment of professional humiliation followed by regrettable communication is not the end of a story. It is almost always the first act. What matters is not the stumble but the recovery chapter you write next." },
  { head:"Your shame reveals what you truly value \u2014 listen to it", body:"Kierkegaard wrote that anxiety is the dizziness of freedom \u2014 the vertigo we feel when confronting our own capacity to choose. You chose to send that email, and now you're confronting the weight of that freedom. But consider what Sartre would add: you are not your past actions. You are, in every moment, the sum of what you choose to do next. The deeper question beneath your rumination isn't 'why did I send that email?' \u2014 it's 'who am I if I'm capable of acting against my own values?' And that question, uncomfortable as it is, marks the beginning of authentic self-knowledge. Socrates would say your examined discomfort is worth more than a thousand unexamined interviews gone right." },
  { head:"Oh god, THAT email \u2014 I genuinely forgot about it until now", body:"Hey, it's us. I'm sitting here trying to even remember the exact wording of that email and I honestly can't. I think it had something snarky in it? The interview was at that company with the weird office, right? Or was that a different one \u2014 we did a lot of interviews around that time. Here's what I do remember: we sent an apology a couple days later, short and classy, and then we moved on. The job we actually ended up getting was so much better it's almost funny. That bad interview wasn't a door closing \u2014 it was the universe physically shoving us toward the right one. I know right now it feels like the walls are closing in, but I promise we laugh about this. Well, we did until I forgot about it entirely." },
  { head:"Stop wallowing and execute the recovery plan NOW", body:"Listen up! You made a tactical error in the field \u2014 every soldier does. But you know what separates the ones who make it from the ones who don't? The ones who MOVE. Here's your three-step action plan and you're executing it in the next sixty minutes. Step one: draft a two-sentence apology email. 'I want to apologize for the tone of my previous message. It didn't reflect my professionalism or my respect for your time.' SEND IT. Step two: open three new job listings and submit applications before you go to sleep tonight. Step three: delete or archive the original email thread so you stop rereading it like it's scripture. That's it. No more thinking. MOVE, MOVE, MOVE." },
  { head:"The email exists in the past \u2014 you exist only right now", body:"Breathe in. Notice that in this exact moment, there is no interview. There is no email. There is only your breath, and the gentle weight of your body, and the sounds around you. Your suffering is not caused by the email itself \u2014 it is caused by your mind traveling backward to replay it, again and again, like a hand reaching into a fire and being surprised each time by the burn. This is what we call attachment to outcome, and attachment to self-image. You are clinging to a version of events you wish had happened differently. Practice this: each time the memory arises, notice it as you would notice a cloud passing. Say gently to yourself, 'thinking,' and return to your breath. The cloud will pass. They always do." },
  { head:"Your brain is stuck in a cortisol-driven rumination loop", body:"Here's what's happening neurologically: the embarrassment from the interview activated your amygdala, which triggered a cortisol and adrenaline response. When you sent the email, you got a brief relief spike \u2014 your brain interpreted the aggressive response as 'fighting back' against a social threat. But then the prefrontal cortex caught up and recognized the email as a second threat, creating a new shame-cortisol cycle on top of the first. You're now experiencing what researchers call 'perseverative cognition' \u2014 repetitive negative thinking that keeps your stress response elevated even though the threat is gone. The evidence-based fix: 20 minutes of moderate exercise will metabolize the excess cortisol. Box breathing (4-4-4-4) reactivates the parasympathetic system. And crucially, writing down your worry once \u2014 on paper, not in your head \u2014 has been shown to reduce rumination by up to 40%." },
  { head:"What if that interview was SUPPOSED to go wrong?", body:"Think about this for a second. What are the odds that the interview went badly AND you happened to send exactly the kind of email that would ensure you'd never work there? Almost like something wanted you away from that company. I'm not saying it's the universe, but I'm not NOT saying it's the universe. Look at the pattern: every detail conspired to close that particular door permanently. Your subconscious might know something your conscious mind doesn't \u2014 maybe that job would have been terrible. Maybe the culture was toxic. Maybe in some parallel timeline you got the job and you're miserable right now. The email wasn't a mistake. It was your intuition burning a bridge you were never supposed to cross." },
  { head:"You seem really sad and I brought you my favorite sock", body:"Hey! HEY! You've been sitting there making that face for a really long time and I don't like it. I don't know what an 'inter-view' is or what an 'ee-mail' is but you keep looking at your glowing rectangle and then sighing and honestly I think the glowing rectangle is the problem here. Have you tried NOT looking at it? That works for me when I can't find my ball \u2014 I just go sniff something else. Also you haven't gone outside in forever and I REALLY think we should go outside because there are probably new smells and maybe a squirrel and I just feel like fresh air fixes most things. Also I love you. I love you so much. Please stop being sad. Treat? TREAT?!" },
];

export default function App() {
  const [screen, setScreen] = useState("splash");
  const [problem, setProblem] = useState("");
  const [safetyBlock, setSafetyBlock] = useState(false);
  const [takeIdx, setTakeIdx] = useState(0);
  const [fadeState, setFadeState] = useState("visible");
  const [showGone, setShowGone] = useState(false);
  const [showInst, setShowInst] = useState(true);

  const busyRef = useRef(false);
  const instRef = useRef(true);
  const screenRef = useRef("splash");
  const idxRef = useRef(0);

  useEffect(() => { screenRef.current = screen; }, [screen]);
  useEffect(() => { instRef.current = showInst; }, [showInst]);
  useEffect(() => { idxRef.current = takeIdx; }, [takeIdx]);

  const BAD = ["kill","suicide","hurt myself","end it all","harm","weapon"];
  const wc = problem.trim().split(/\s+/).filter(Boolean).length;
  const FREE = 10;
  const lens = LENSES[takeIdx % LENSES.length];
  const take = TAKES[takeIdx % TAKES.length];
  const remaining = FREE - (takeIdx + 1);

  function doSubmit() {
    if (wc < 20) return;
    if (BAD.some(k => problem.toLowerCase().includes(k))) { setSafetyBlock(true); return; }
    setScreen("loading");
    setTimeout(() => {
      setTakeIdx(0); idxRef.current = 0;
      setShowInst(true); instRef.current = true;
      setFadeState("visible");
      setScreen("takes");
    }, 1800);
  }

  function advance() {
    if (busyRef.current) return;
    if (instRef.current) { setShowInst(false); instRef.current = false; return; }
    busyRef.current = true;
    setShowGone(true);
    setTimeout(() => setShowGone(false), 1200);
    setFadeState("out");
    setTimeout(() => {
      const next = idxRef.current + 1;
      setTakeIdx(next); idxRef.current = next;
      setFadeState("in");
      requestAnimationFrame(() => { requestAnimationFrame(() => { setFadeState("visible"); busyRef.current = false; }); });
    }, 300);
  }

  useEffect(() => {
    function onWheel(e) { if (screenRef.current === "takes" && e.deltaY > 0) advance(); }
    let ty = 0;
    function onTS(e) { if (screenRef.current === "takes") ty = e.touches[0].clientY; }
    function onTE(e) { if (screenRef.current === "takes" && ty - e.changedTouches[0].clientY > 40) advance(); }
    function onKey(e) { if (screenRef.current === "takes" && ["ArrowUp","ArrowDown"," "].includes(e.key)) { e.preventDefault(); advance(); } }
    window.addEventListener("wheel", onWheel, { passive: true });
    window.addEventListener("touchstart", onTS, { passive: true });
    window.addEventListener("touchend", onTE, { passive: true });
    window.addEventListener("keydown", onKey);
    return () => { window.removeEventListener("wheel", onWheel); window.removeEventListener("touchstart", onTS); window.removeEventListener("touchend", onTE); window.removeEventListener("keydown", onKey); };
  }, []);

  const fade = (delay = 0) => ({
    opacity: fadeState === "out" ? 0 : 1,
    transform: fadeState === "out" ? "translateY(-40px)" : fadeState === "in" ? "translateY(40px)" : "translateY(0)",
    transition: `opacity 0.3s ease ${delay}s, transform 0.3s ease ${delay}s`,
  });

  const S = {
    phone: { width:390,height:844,background:'#0a0a0c',borderRadius:44,border:'3px solid #2a2a30',position:'relative',overflow:'hidden',boxShadow:'0 0 0 8px #111,0 30px 80px rgba(0,0,0,0.6)' },
    notch: { width:126,height:34,background:'#000',borderRadius:'0 0 20px 20px',position:'absolute',top:0,left:'50%',transform:'translateX(-50%)',zIndex:200 },
    sb: { height:54,display:'flex',alignItems:'center',justifyContent:'space-between',padding:'14px 28px 0',fontSize:15,fontWeight:600,position:'absolute',top:0,left:0,right:0,zIndex:150,background:'#0a0a0c' },
    area: { position:'absolute',top:54,left:0,right:0,bottom:0,display:'flex',flexDirection:'column' },
    ctr: { flex:1,display:'flex',alignItems:'center',justifyContent:'center',textAlign:'center' },
  };

  return (
    <div style={{background:'#000',width:'100vw',height:'100vh',display:'flex',justifyContent:'center',alignItems:'center',fontFamily:"'DM Sans',sans-serif",color:'#f0ece4'}}>
      <style>{GLOBAL_CSS}</style>
      <div style={S.phone}>
        <div style={S.notch}/><div style={S.sb}><span>9:41</span><span style={{fontSize:13}}>⦿ ▮</span></div>
        <div style={S.area}>

          {screen === "splash" && (
            <div style={S.ctr}><div>
              <div style={{width:80,height:80,borderRadius:20,background:'linear-gradient(135deg,#e8653a,#9b6dff)',margin:'0 auto 24px',display:'flex',alignItems:'center',justifyContent:'center',fontSize:36}}>∞</div>
              <h1 style={{fontFamily:"'Instrument Serif',serif",fontSize:38,background:'linear-gradient(135deg,#f0ece4,#c9a84c)',WebkitBackgroundClip:'text',WebkitTextFillColor:'transparent',marginBottom:8}}>Endless Rumination</h1>
              <p style={{fontSize:15,color:'#8a8690',fontWeight:300,letterSpacing:3,textTransform:'uppercase',marginBottom:48}}>Scroll your worries</p>
              <button onClick={() => setScreen("input")} style={{background:'#f0ece4',color:'#0a0a0c',border:'none',padding:'16px 48px',borderRadius:50,fontSize:16,fontWeight:700,cursor:'pointer',fontFamily:'inherit'}}>Begin</button>
            </div></div>
          )}

          {screen === "input" && (
            <div style={{flex:1,display:'flex',flexDirection:'column',padding:'0 24px',position:'relative'}}>
              <div style={{padding:'20px 0 12px',display:'flex',alignItems:'center',justifyContent:'space-between'}}>
                <h2 style={{fontFamily:"'Instrument Serif',serif",fontSize:28}}>What's on your mind?</h2>
                <div style={{background:'linear-gradient(135deg,#c9a84c,#e8653a)',color:'#0a0a0c',fontSize:11,fontWeight:700,padding:'5px 12px',borderRadius:20,letterSpacing:1,textTransform:'uppercase'}}>PRO $1.99</div>
              </div>
              <p style={{fontSize:13,color:'#8a8690',marginBottom:12,lineHeight:1.5}}>Describe what's bothering you. Be specific — the more you share, the better the perspectives.</p>
              <div style={{position:'relative',flex:1,display:'flex',flexDirection:'column',marginBottom:20}}>
                <textarea value={problem} onChange={e => setProblem(e.target.value)} placeholder="I can't stop thinking about..." style={{flex:1,background:'#1a1a20',border:'1px solid rgba(255,255,255,0.06)',borderRadius:16,padding:20,fontFamily:'inherit',fontSize:16,lineHeight:1.6,color:'#f0ece4',resize:'none',outline:'none'}}/>
                <div style={{position:'absolute',bottom:14,right:16,fontFamily:"'JetBrains Mono',monospace",fontSize:12,color:wc>=20?'#3ecf8e':wc>=15?'#c9a84c':'#4a4650',background:'#1a1a20',padding:'4px 8px',borderRadius:6}}>{wc} / 20 words</div>
              </div>
              <button onClick={doSubmit} style={{width:'100%',padding:18,border:'none',borderRadius:14,fontSize:16,fontWeight:700,cursor:wc>=20?'pointer':'not-allowed',marginBottom:16,background:wc>=20?'linear-gradient(135deg,#e8653a,#d44a2a)':'#1a1a20',color:wc>=20?'#fff':'#4a4650',fontFamily:'inherit'}}>
                {wc >= 20 ? 'See perspectives' : wc >= 15 ? `Need ${20-wc} more words` : 'Need at least 20 words'}
              </button>
              <p style={{textAlign:'center',fontSize:11,color:'#4a4650',paddingBottom:24}}>🛡 All content analyzed for safety. Crisis resources provided when needed.</p>
              {safetyBlock && (
                <div style={{position:'absolute',top:0,left:-24,right:-24,bottom:0,background:'rgba(10,10,12,0.95)',display:'flex',alignItems:'center',justifyContent:'center',padding:40,zIndex:200}}>
                  <div style={{textAlign:'center'}}>
                    <div style={{width:64,height:64,borderRadius:'50%',background:'rgba(255,71,87,0.15)',display:'flex',alignItems:'center',justifyContent:'center',margin:'0 auto 20px',fontSize:28}}>🛡️</div>
                    <h3 style={{fontFamily:"'Instrument Serif',serif",fontSize:24,marginBottom:12}}>We can't process this</h3>
                    <p style={{fontSize:14,color:'#8a8690',lineHeight:1.6,marginBottom:8}}>Your input was flagged by our safety system.</p>
                    <p style={{fontSize:13,color:'#4a7cff',marginBottom:28,cursor:'pointer'}}>If you're in crisis, tap here for resources →</p>
                    <button onClick={() => setSafetyBlock(false)} style={{background:'#1a1a20',border:'1px solid rgba(255,255,255,0.06)',color:'#f0ece4',padding:'14px 40px',borderRadius:50,fontSize:15,cursor:'pointer',fontFamily:'inherit'}}>Edit my input</button>
                  </div>
                </div>
              )}
            </div>
          )}

          {screen === "loading" && (
            <div style={S.ctr}><div>
              <div style={{width:48,height:48,border:'3px solid rgba(255,255,255,0.06)',borderTopColor:'#e8653a',borderRadius:'50%',animation:'er-spin 0.8s linear infinite',margin:'0 auto 24px'}}/>
              <p style={{fontSize:14,color:'#8a8690',animation:'er-pulse 1.5s ease-in-out infinite'}}>Generating perspectives...</p>
            </div></div>
          )}

          {screen === "takes" && (<>
            <div style={{padding:'12px 24px',display:'flex',alignItems:'center',justifyContent:'space-between',flexShrink:0}}>
              <button onClick={() => { setProblem(''); setScreen('input'); }} style={{background:'none',border:'none',color:'#8a8690',fontSize:14,cursor:'pointer',fontFamily:'inherit'}}>← New problem</button>
              <div style={{fontFamily:"'JetBrains Mono',monospace",fontSize:12,color:'#4a4650',background:'#1a1a20',padding:'4px 10px',borderRadius:8}}>{takeIdx+1} / 20</div>
            </div>
            <div onClick={advance} style={{flex:1,display:'flex',flexDirection:'column',justifyContent:'center',padding:'24px 28px 70px',position:'relative',overflow:'hidden',cursor:'pointer'}}>
              <div style={{...fade(0),display:'inline-flex',alignItems:'center',gap:8,padding:'6px 14px',borderRadius:50,fontSize:12,fontWeight:700,textTransform:'uppercase',letterSpacing:2,marginBottom:16,width:'fit-content',background:lens.bg,color:lens.color}}>{lens.e} {lens.n}</div>
              <div style={{...fade(0.05),fontFamily:"'Instrument Serif',serif",fontSize:24,lineHeight:1.4,marginBottom:16}}>{take.head}</div>
              <div style={{...fade(0.1),fontSize:13.5,lineHeight:1.7,color:'#8a8690',fontWeight:300,maxHeight:300,overflowY:'auto'}}>{take.body}</div>
              <div style={{position:'absolute',bottom:16,left:0,right:0,textAlign:'center',fontSize:11,color:'#4a4650',letterSpacing:2,textTransform:'uppercase',animation:'er-bob 2s ease-in-out infinite'}}>
                <svg viewBox="0 0 24 24" style={{display:'block',margin:'0 auto 6px',width:20,height:20,fill:'#4a4650',transform:'rotate(180deg)'}}><path d="M7.41 15.41L12 10.83l4.59 4.58L18 14l-6-6-6 6z"/></svg>
                swipe up · fades forever
              </div>
              {showGone && <div style={{position:'absolute',top:'45%',left:'50%',fontFamily:"'JetBrains Mono',monospace",fontSize:11,color:'#ff4757',letterSpacing:3,textTransform:'uppercase',animation:'er-gflash 1.2s ease-out forwards',zIndex:10}}>gone forever</div>}
              {remaining <= 3 && remaining > 0 && <div style={{position:'absolute',bottom:4,left:0,right:0,textAlign:'center',fontFamily:"'JetBrains Mono',monospace",fontSize:11,color:'#4a4650'}}><span style={{color:'#c9a84c'}}>{remaining}</span> free takes remaining</div>}
              {remaining <= 0 && <div style={{position:'absolute',bottom:4,left:0,right:0,textAlign:'center',fontFamily:"'JetBrains Mono',monospace",fontSize:11,color:'#4a4650'}}>Daily limit reached · <span style={{color:'#c9a84c'}}>Go Pro</span></div>}
              {showInst && (
                <div onClick={e => { e.stopPropagation(); setShowInst(false); instRef.current = false; }} style={{position:'absolute',top:0,left:0,right:0,bottom:0,background:'rgba(10,10,12,0.7)',display:'flex',alignItems:'center',justifyContent:'center',zIndex:20,cursor:'pointer'}}>
                  <div style={{textAlign:'center',animation:'er-bob 2s ease-in-out infinite'}}>
                    <div style={{fontSize:36,marginBottom:12,opacity:0.6}}>↑</div>
                    <p style={{fontSize:14,color:'#8a8690',letterSpacing:2,textTransform:'uppercase'}}>Swipe up for next take</p>
                    <p style={{fontSize:11,color:'#4a4650',marginTop:8}}>Each perspective disappears forever</p>
                    <p style={{fontSize:11,color:'#c9a84c',marginTop:16}}>Free: 10 takes/day · Pro: unlimited</p>
                  </div>
                </div>
              )}
            </div>
            <div style={{height:50,flexShrink:0,background:'#1a1a20',borderTop:'1px solid rgba(255,255,255,0.06)',display:'flex',alignItems:'center',justifyContent:'center',fontSize:11,color:'#4a4650',letterSpacing:1,position:'relative'}}>
              <span style={{position:'absolute',top:4,right:10,fontSize:8,textTransform:'uppercase',letterSpacing:1}}>Ad</span>
              mindfulness app — download free
              <span onClick={() => alert('$1.99 → remove ads + save takes + unlimited')} style={{color:'#c9a84c',cursor:'pointer',marginLeft:8,fontWeight:600}}>Remove</span>
            </div>
          </>)}

        </div>
      </div>
    </div>
  );
}