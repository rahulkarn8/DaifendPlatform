"use client";

import * as React from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import * as THREE from "three";

function usePrefersReducedMotion() {
  const [reduced, setReduced] = React.useState(false);
  React.useEffect(() => {
    const m = window.matchMedia("(prefers-reduced-motion: reduce)");
    const on = () => setReduced(Boolean(m.matches));
    on();
    m.addEventListener?.("change", on);
    return () => m.removeEventListener?.("change", on);
  }, []);
  return reduced;
}

function Field() {
  const group = React.useRef<THREE.Group>(null);
  const reduced = usePrefersReducedMotion();

  const lines = React.useMemo(() => {
    const material = new THREE.LineBasicMaterial({
      color: new THREE.Color("#9FB4FF"),
      transparent: true,
      opacity: 0.08,
    });
    const items: THREE.Line[] = [];
    for (let i = 0; i < 34; i++) {
      const geo = new THREE.BufferGeometry();
      const pts: THREE.Vector3[] = [];
      const z = (i - 17) * 0.18;
      for (let k = 0; k < 40; k++) {
        const x = (k - 20) * 0.22;
        const y = Math.sin(k * 0.25 + i * 0.14) * 0.12;
        pts.push(new THREE.Vector3(x, y, z));
      }
      geo.setFromPoints(pts);
      const line = new THREE.Line(geo, material);
      items.push(line);
    }
    return items;
  }, []);

  useFrame((state) => {
    if (!group.current) return;
    if (reduced) return;
    const t = state.clock.getElapsedTime();
    group.current.rotation.y = Math.sin(t * 0.08) * 0.10;
    group.current.rotation.x = Math.sin(t * 0.06) * 0.06 - 0.12;
    group.current.position.y = Math.sin(t * 0.12) * 0.05 - 0.25;
  });

  return (
    <group ref={group} position={[0, -0.2, 0]}>
      {lines.map((l, idx) => (
        // eslint-disable-next-line react/no-unknown-property
        <primitive key={idx} object={l} />
      ))}
    </group>
  );
}

export function SubtleField3D() {
  return (
    <div className="pointer-events-none fixed inset-0 -z-10 opacity-70">
      <Canvas
        dpr={[1, 1.5]}
        camera={{ position: [0, 1.1, 6.5], fov: 45 }}
        gl={{ antialias: true, alpha: true, powerPreference: "low-power" }}
      >
        {/* eslint-disable-next-line react/no-unknown-property */}
        <ambientLight intensity={0.6} />
        {/* eslint-disable-next-line react/no-unknown-property */}
        <fog attach="fog" args={["#050505", 4.5, 10]} />
        <Field />
      </Canvas>
    </div>
  );
}

