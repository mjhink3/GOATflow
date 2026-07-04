"use client";

import { useMemo } from "react";

interface MountainProgressProps {
  currentLevel: number;
  currentHay: number;
  hayToNext: number;
  memberPositions?: Array<{
    display_name: string;
    level: number;
    color?: string;
  }>;
  compact?: boolean;
}

const LEVELS = [
  { level: 1, name: "The Pen",             emoji: "🐐" },
  { level: 2, name: "The Grazing Grounds", emoji: "🐐" },
  { level: 3, name: "The Foothills",       emoji: "🐐" },
  { level: 4, name: "The Ridgeline",       emoji: "🐐" },
  { level: 5, name: "The High Cliffs",     emoji: "🐐" },
  { level: 6, name: "The Summit",          emoji: "🐐" },
  { level: 7, name: "GOAT Mountain",       emoji: "👑" },
];

export function MountainProgress({
  currentLevel,
  currentHay,
  hayToNext,
  memberPositions,
  compact = false,
}: MountainProgressProps) {
  const width  = compact ? 220 : 400;
  const height = compact ? 140 : 260;

  const peakX       = width * 0.5;
  const peakY       = height * 0.06;
  const baseY       = height * 0.88;
  const baseLeftX   = width * 0.02;
  const baseRightX  = width * 0.98;

  function getLevelPosition(level: number): { x: number; y: number } {
    const t = (Math.max(1, Math.min(7, level)) - 1) / 6;
    return {
      x: baseLeftX + (peakX - baseLeftX) * t,
      y: baseY + (peakY - baseY) * t,
    };
  }

  const mountainPath = useMemo(() => `
    M ${baseLeftX} ${baseY}
    L ${width * 0.15} ${baseY * 0.75}
    L ${width * 0.25} ${baseY * 0.82}
    L ${width * 0.35} ${baseY * 0.52}
    L ${peakX} ${peakY}
    L ${width * 0.62} ${baseY * 0.45}
    L ${width * 0.72} ${baseY * 0.58}
    L ${width * 0.82} ${baseY * 0.70}
    L ${baseRightX} ${baseY}
    Z
  `, [width, height]); // eslint-disable-line react-hooks/exhaustive-deps

  const snowPath = `
    M ${peakX - 18} ${peakY + 22}
    L ${peakX} ${peakY}
    L ${peakX + 18} ${peakY + 22}
    Z
  `;

  const currentPos = getLevelPosition(currentLevel);
  const isGoat     = currentLevel >= 7;

  return (
    <div style={{ width: "100%", maxWidth: width }}>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        style={{ width: "100%", height: "auto", overflow: "visible" }}
      >
        <defs>
          <linearGradient id="mountainGrad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#2A1A4A" />
            <stop offset="100%" stopColor="#1A1A2E" />
          </linearGradient>
          <filter id="glow">
            <feGaussianBlur stdDeviation="2" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <filter id="goldGlow">
            <feGaussianBlur stdDeviation="3" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Mountain silhouette */}
        <path d={mountainPath} fill="url(#mountainGrad)" stroke="#2A2A4A" strokeWidth="1" />

        {/* Snow / gold cap */}
        <path
          d={snowPath}
          fill={isGoat ? "#FFD700" : "white"}
          opacity={isGoat ? 1 : 0.7}
        />

        {/* Progress trail line from base to current level */}
        {currentLevel > 1 && (() => {
          const startPos = getLevelPosition(1);
          return (
            <line
              x1={startPos.x}
              y1={startPos.y}
              x2={currentPos.x}
              y2={currentPos.y}
              stroke="#6100ff"
              strokeWidth="2"
              strokeDasharray="4 2"
              opacity="0.6"
            />
          );
        })()}

        {/* Level markers */}
        {LEVELS.map(({ level, name }) => {
          const pos        = getLevelPosition(level);
          const isCurrent  = level === currentLevel;
          const isNextLvl  = level === currentLevel + 1 && currentLevel < 7;
          const isUnlocked = level <= currentLevel;
          const isLocked   = level > currentLevel;
          // Show labels only for current level and next target; peak covered by GOAT MTN text
          const showLabel  = !compact && (isCurrent || isNextLvl);
          // When at level 1 both current + next labels are low on the slope — push level 1 label down
          const labelYExtra = currentLevel === 1 && level === 1 ? 10 : 0;

          return (
            <g key={level}>
              <line
                x1={pos.x - 8}
                y1={pos.y}
                x2={pos.x + 8}
                y2={pos.y}
                stroke={isUnlocked ? "#6100ff" : "#2A2A4A"}
                strokeWidth={isCurrent ? 2 : 1}
              />
              {showLabel && (
                <text
                  x={pos.x + 14}
                  y={pos.y + 4 + labelYExtra}
                  fontSize={isCurrent ? 10 : 8}
                  fill={isCurrent ? "#a78bfa" : "#6b7280"}
                  fontFamily="var(--font-dm-sans, sans-serif)"
                  fontWeight={isCurrent ? "700" : "400"}
                >
                  {name}
                </text>
              )}
              <circle
                cx={pos.x}
                cy={pos.y}
                r={isCurrent ? 5 : 3}
                fill={isLocked ? "#1A1A2E" : isCurrent ? "#6100ff" : "#3A2A6A"}
                stroke={isLocked ? "#2A2A4A" : isCurrent ? "#a78bfa" : "#6100ff"}
                strokeWidth="1"
                filter={isCurrent ? "url(#glow)" : "none"}
              />
            </g>
          );
        })}

        {/* Current user goat */}
        <text
          x={currentPos.x - 8}
          y={currentPos.y - 10}
          fontSize={compact ? 14 : 18}
          filter={isGoat ? "url(#goldGlow)" : "url(#glow)"}
        >
          {isGoat ? "👑" : "🐐"}
        </text>

        {/* Member positions (HerdBoss view) */}
        {memberPositions?.map((member, i) => {
          const pos     = getLevelPosition(member.level);
          const offsetX = i % 2 === 0 ? -14 : 14;
          return (
            <g key={`${member.display_name}-${i}`}>
              <title>{member.display_name}</title>
              <text
                x={pos.x + offsetX - 6}
                y={pos.y - 8}
                fontSize={compact ? 8 : 10}
              >
                🐐
              </text>
            </g>
          );
        })}

        {/* GOAT Mountain peak label */}
        {!compact && (
          <text
            x={peakX}
            y={peakY - 8}
            fontSize={9}
            fill={isGoat ? "#FFD700" : "#4b5563"}
            textAnchor="middle"
            fontFamily="var(--font-syne, sans-serif)"
            fontWeight="700"
            letterSpacing="0.1em"
          >
            GOAT MTN
          </text>
        )}


      </svg>

      {/* Text below (full size only) */}
      {!compact && (
        <div style={{ textAlign: "center", marginTop: 4 }}>
          <p style={{ fontSize: 11, color: "#6b7280" }}>
            {LEVELS[Math.min(currentLevel, 7) - 1]?.name ?? "The Pen"}
            {currentLevel < 7 && (
              <span style={{ color: "#4b5563" }}> → {LEVELS[Math.min(currentLevel, 6)]?.name}</span>
            )}
          </p>
          {currentLevel < 7 && (
            <p style={{ fontSize: 10, color: "#4b5563", marginTop: 2 }}>
              {hayToNext.toLocaleString()} Hay to next level
            </p>
          )}
        </div>
      )}
    </div>
  );
}
