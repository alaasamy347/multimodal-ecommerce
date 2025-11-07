// types/model-viewer.d.ts
// TypeScript declarations for model-viewer web component

declare global {
  namespace JSX {
    interface IntrinsicElements {
      'model-viewer': ModelViewerElement & React.DetailedHTMLProps<React.HTMLAttributes<HTMLElement>, HTMLElement>;
    }
  }
}

interface ModelViewerElement {
  src?: string;
  poster?: string;
  alt?: string;
  ar?: boolean;
  'ar-modes'?: string;
  'ar-scale'?: string;
  'camera-controls'?: boolean;
  'camera-orbit'?: string;
  'camera-target'?: string;
  'environment-image'?: string;
  'exposure'?: string;
  'shadow-intensity'?: string;
  'shadow-softness'?: string;
  'auto-rotate'?: boolean;
  'auto-rotate-delay'?: string;
  'rotation-per-second'?: string;
  'interaction-prompt'?: string;
  'interaction-prompt-style'?: string;
  'interaction-prompt-threshold'?: string;
  'loading'?: string;
  'reveal'?: string;
  'touch-action'?: string;
  'disable-zoom'?: boolean;
  'disable-pan'?: boolean;
  'disable-tap'?: boolean;
  'interpolation-decay'?: string;
  'min-camera-orbit'?: string;
  'max-camera-orbit'?: string;
  'min-field-of-view'?: string;
  'max-field-of-view'?: string;
  bounds?: string;
  'animation-name'?: string;
  'animation-crossfade-duration'?: string;
  autoplay?: boolean;
  'skybox-image'?: string;
  'skybox-height'?: string;
  
  // Event handlers
  onLoad?: (event: Event) => void;
  onError?: (event: ErrorEvent) => void;
  'onModel-visibility'?: (event: Event) => void;
  'onProgress'?: (event: Event) => void;
  'onCamera-change'?: (event: Event) => void;
}

export {};