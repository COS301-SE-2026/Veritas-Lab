'use client'
import { Handle, Position } from '@xyflow/react';

export const PinSize = 14;

export default function Pin({ color = '#c0392b' }: { color?: string }) {
    return (
        <Handle
            type="source"
            position={Position.Top}
            style={{
                top: 12,
                width: PinSize,
                height: PinSize,
                border: 'none',
                borderRadius: '50%',
                background: `radial-gradient(circle at 35% 30%, #fff8 0 18%, ${color} 45%, color-mix(in srgb, ${color} 60%, black) 100%)`,
                boxShadow: '1px 3px 3px rgba(0,0,0,.35)',
                cursor: 'crosshair',
            }}
        />
    );
}