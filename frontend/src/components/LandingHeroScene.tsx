import { Component, Suspense, useRef, type ReactNode } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { motion, useReducedMotion } from 'framer-motion';
import type { Group, Mesh } from 'three';

const sheetCount = 7;
const mainSheet = 3;

function ContractPages({ reducedMotion }: { reducedMotion: boolean }) {
  const fan = useRef<Group>(null);
  const pages = useRef<Array<Group | null>>([]);
  const scan = useRef<Mesh>(null);
  const connector = useRef<Mesh>(null);

  useFrame(({ clock, pointer }) => {
    const elapsed = clock.elapsedTime;
    const open = reducedMotion ? 1 : 1 - Math.exp(-elapsed * 0.56);
    if (fan.current) {
      fan.current.rotation.y = reducedMotion ? -0.08 : Math.sin(elapsed * 0.17) * 0.055 + pointer.x * 0.08;
      fan.current.rotation.x = reducedMotion ? 0 : pointer.y * -0.045;
      fan.current.position.y = reducedMotion ? 0 : Math.sin(elapsed * 0.36) * 0.025;
    }

    pages.current.forEach((page, index) => {
      if (!page) return;
      const distance = index - mainSheet;
      const delay = Math.abs(distance) * 0.12;
      const spread = reducedMotion ? 1 : Math.max(0, Math.min(1, (elapsed - delay) / 1.8));
      const ease = spread * spread * (3 - 2 * spread);
      page.position.x = distance * 0.39 * ease;
      page.position.z = index === mainSheet ? 0.12 : -0.14 - Math.abs(distance) * 0.035;
      page.rotation.y = distance * 0.17 * ease;
      page.rotation.z = -distance * 0.07 * ease;
    });

    if (scan.current) {
      scan.current.position.y = reducedMotion ? -0.22 : 1.12 - ((elapsed * 0.7) % 2.25);
      scan.current.visible = reducedMotion || elapsed > 1.2;
    }
    if (connector.current) {
      const draw = reducedMotion ? 1 : Math.max(0, Math.min(1, (elapsed - 1.75) / 0.8));
      connector.current.scale.x = draw;
      connector.current.visible = draw > 0;
    }
  });

  return (
    <group ref={fan}>
      {Array.from({ length: sheetCount }, (_, index) => {
        const selected = index === mainSheet;
        return (
          <group key={index} ref={(node) => { pages.current[index] = node; }}>
            <mesh castShadow receiveShadow>
              <boxGeometry args={[2.28, 3.16, selected ? 0.07 : 0.045]} />
              <meshPhysicalMaterial
                color={selected ? '#ffffff' : index % 2 ? '#fffaf2' : '#f3e8d8'}
                roughness={0.4}
                clearcoat={selected ? 0.35 : 0.18}
                metalness={0.015}
              />
            </mesh>
            {!selected && (
              <mesh position={[0, -1.57, 0.022]}>
                <boxGeometry args={[2.08, 0.025, 0.012]} />
                <meshBasicMaterial color="#dfc9a8" transparent opacity={0.72} />
              </mesh>
            )}
            {selected && (
              <group position={[0, 0, 0.047]}>
                <mesh position={[0, 1.13, 0]}>
                  <boxGeometry args={[1.7, 0.025, 0.012]} />
                  <meshBasicMaterial color="#dce8f6" />
                </mesh>
                <mesh position={[-0.7, 0.82, 0]}>
                  <boxGeometry args={[0.34, 0.055, 0.012]} />
                  <meshBasicMaterial color="#2f5f9f" />
                </mesh>
                {[-0.12, -0.34, -0.56, -0.78, -1, -1.22].map((y, line) => (
                  <mesh key={y} position={[-0.01, y, 0]}>
                    <boxGeometry args={[line === 2 ? 1.56 : line % 2 ? 1.66 : 1.42, 0.028, 0.01]} />
                    <meshBasicMaterial color={line === 2 ? '#8aa8cf' : '#ccd9e9'} />
                  </mesh>
                ))}
                <mesh position={[0.01, -0.57, 0.013]}>
                  <boxGeometry args={[1.76, 0.23, 0.015]} />
                  <meshBasicMaterial color="#e9f3ff" transparent opacity={0.92} />
                </mesh>
                <mesh position={[-0.76, -0.57, 0.023]}>
                  <boxGeometry args={[0.035, 0.17, 0.012]} />
                  <meshBasicMaterial color="#4a8ef3" />
                </mesh>
                <mesh position={[0, -1.01, 0.013]}>
                  <boxGeometry args={[1.76, 0.23, 0.015]} />
                  <meshBasicMaterial color="#fff3e9" transparent opacity={0.96} />
                </mesh>
                <mesh position={[-0.76, -1.01, 0.023]}>
                  <boxGeometry args={[0.035, 0.17, 0.012]} />
                  <meshBasicMaterial color="#f29a56" />
                </mesh>
                <mesh ref={scan} position={[0, 1.12, 0.035]}>
                  <boxGeometry args={[1.92, 0.035, 0.018]} />
                  <meshBasicMaterial color="#74c8ff" transparent opacity={0.58} />
                </mesh>
              </group>
            )}
          </group>
        );
      })}
      <mesh ref={connector} position={[-0.01, -0.765, 0.37]} rotation={[0, 0, -0.32]} scale={[0, 1, 1]}>
        <boxGeometry args={[1.5, 0.018, 0.012]} />
        <meshBasicMaterial color="#438df0" transparent opacity={0.82} />
      </mesh>
      <mesh position={[-0.72, -0.53, 0.38]}>
        <sphereGeometry args={[0.045, 16, 16]} />
        <meshBasicMaterial color="#57a7ff" />
      </mesh>
      <mesh position={[0.7, -1, 0.36]}>
        <sphereGeometry args={[0.045, 16, 16]} />
        <meshBasicMaterial color="#57a7ff" />
      </mesh>
    </group>
  );
}

function SceneContents({ reducedMotion }: { reducedMotion: boolean }) {
  return (
    <>
      <ambientLight intensity={1.6} />
      <directionalLight position={[-3, 4, 5]} intensity={2.1} color="#ffffff" />
      <pointLight position={[3, 0, 3]} intensity={1.6} color="#85dafa" />
      <Suspense fallback={null}>
        <ContractPages reducedMotion={reducedMotion} />
      </Suspense>
    </>
  );
}

function StaticFallback() {
  return (
    <div className="landing-document-fallback" role="img" aria-label="Layered contract pages with highlighted clauses">
      <div className="fallback-paper fallback-paper-back" />
      <div className="fallback-paper fallback-paper-middle" />
      <div className="fallback-paper fallback-paper-front">
        <span className="fallback-paper-kicker">CLAUSE-WISE · CONTRACT REVIEW</span>
        <strong>MASTER SERVICE AGREEMENT</strong>
        <i /><i /><i /><i />
        <span className="fallback-highlight">30 days' notice</span>
        <i /><i />
      </div>
    </div>
  );
}

class WebGLBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };

  static getDerivedStateFromError() {
    return { failed: true };
  }

  render() {
    return this.state.failed ? <StaticFallback /> : this.props.children;
  }
}

export default function LandingHeroScene() {
  const reducedMotion = Boolean(useReducedMotion());
  return (
    <div className="landing-hero-visual" aria-label="CLAUSE-WISE contract analysis preview">
      <svg className="landing-paper-sculpture" viewBox="0 0 640 560" fill="none" aria-hidden="true">
        <defs>
          <linearGradient id="paperContour" x1="290" y1="10" x2="610" y2="440" gradientUnits="userSpaceOnUse">
            <stop stopColor="#fffefa" /><stop offset=".52" stopColor="#ece8df" /><stop offset="1" stopColor="#d9d5cd" />
          </linearGradient>
          <filter id="paperShadow" x="-20%" y="-20%" width="150%" height="160%"><feGaussianBlur stdDeviation="5" /></filter>
        </defs>
        <path d="M302 -55C304 74 342 113 428 165c87 52 115 99 128 195 8 62 23 104 74 142" stroke="#918b81" strokeOpacity=".16" strokeWidth="34" filter="url(#paperShadow)"/>
        <path d="M260 -66C265 68 304 119 391 170c88 52 120 102 135 197 10 62 27 102 79 139" stroke="url(#paperContour)" strokeWidth="29"/>
        <path d="M224 -72C229 63 269 124 355 176c91 55 126 107 143 202 11 60 31 100 82 137" stroke="url(#paperContour)" strokeWidth="24"/>
        <path d="M190 -78C194 58 234 129 320 183c93 58 131 111 150 205 13 61 34 101 84 137" stroke="url(#paperContour)" strokeWidth="20"/>
        <path d="M157 -83C160 53 199 133 285 190c96 63 135 117 156 211 14 61 37 101 86 137" stroke="url(#paperContour)" strokeWidth="16"/>
        <path d="M126 -88C127 48 165 137 250 197c98 68 139 123 160 217 15 61 40 101 87 137" stroke="url(#paperContour)" strokeWidth="12"/>
      </svg>
      <div className="landing-scene-canvas" aria-hidden="true">
        <WebGLBoundary>
          <Canvas
            camera={{ position: [0, 0, 7.2], fov: 39 }}
            dpr={[1, 1.35]}
            gl={{ alpha: true, antialias: true, powerPreference: 'low-power' }}
            fallback={<StaticFallback />}
          >
            <SceneContents reducedMotion={reducedMotion} />
          </Canvas>
        </WebGLBoundary>
      </div>
      <motion.div
        className="landing-conflict-toast"
        initial={reducedMotion ? false : { opacity: 0, y: 12, scale: 0.96 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ delay: reducedMotion ? 0 : 2.4, duration: reducedMotion ? 0 : 0.5, ease: 'easeOut' }}
      >
        <span className="toast-alert-icon">↔</span>
        <span><b>Potential Contradiction Detected</b><small>Notice period differs across clauses</small></span>
        <span className="toast-linked-dot" />
      </motion.div>
      <motion.div
        className="landing-risk-panel"
        initial={reducedMotion ? false : { opacity: 0, y: 14 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: reducedMotion ? 0 : 3.05, duration: reducedMotion ? 0 : 0.55, ease: 'easeOut' }}
      >
        <div className="risk-panel-top"><span className="risk-panel-icon">↗</span><span><b>Risk analysis</b><small>3 specialist checks</small></span><strong>28<span>/100</span></strong></div>
        <div className="risk-metric"><span>Clause quality</span><b>Good</b><i><em style={{ width: '78%' }} /></i></div>
        <div className="risk-metric"><span>Financial exposure</span><b>Review</b><i className="exposure"><em style={{ width: '46%' }} /></i></div>
        <div className="risk-metric"><span>Cross-clause conflicts</span><b>1 linked</b><i className="conflict"><em style={{ width: '34%' }} /></i></div>
      </motion.div>
      <div className="landing-orbit-tag landing-tag-privacy"><span />Evidence linked to source</div>
      <div className="landing-orbit-tag landing-tag-pages">07 <span>pages reviewed</span></div>
    </div>
  );
}
