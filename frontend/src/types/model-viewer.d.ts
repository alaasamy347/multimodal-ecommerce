// import React from "react";

// declare global {
//   namespace JSX {
//     interface IntrinsicElements {
//       "model-viewer": React.DetailedHTMLProps<
//         React.HTMLAttributes<HTMLElement>,
//         HTMLElement
//       > & {
//         src?: string;
//         poster?: string;
//         alt?: string;

//         ar?: boolean;
//         "ar-modes"?: string;
//         "ar-scale"?: string;

//         "camera-controls"?: boolean;
//         "camera-orbit"?: string;
//         "camera-target"?: string;

//         "environment-image"?: string;
//         exposure?: string;

//         "shadow-intensity"?: string;
//         "shadow-softness"?: string;

//         "auto-rotate"?: boolean;
//         "auto-rotate-delay"?: string;
//         "rotation-per-second"?: string;

//         "interaction-prompt"?: string;
//         loading?: string;
//         reveal?: string;

//         "touch-action"?: string;

//         "min-camera-orbit"?: string;
//         "max-camera-orbit"?: string;
//         "field-of-view"?: string;
//       };
//     }
//   }
// }

// export {};

/**
 * Type definitions for @google/model-viewer
 * Proper TypeScript support for model-viewer web component
 */

declare namespace JSX {
  interface IntrinsicElements {
    'model-viewer': ModelViewerJSX & React.DetailedHTMLProps<React.HTMLAttributes<HTMLElement>, HTMLElement>;
  }
}

interface ModelViewerJSX {
  src?: string;
  poster?: string;
  alt?: string;

  // AR properties
  ar?: boolean;
  'ar-modes'?: string;
  'ar-scale'?: string;
  'ar-placement'?: string;

  // Camera controls
  'camera-controls'?: boolean;
  'camera-orbit'?: string;
  'camera-target'?: string;
  'field-of-view'?: string;
  'min-camera-orbit'?: string;
  'max-camera-orbit'?: string;
  'min-field-of-view'?: string;
  'max-field-of-view'?: string;

  // Interaction
  'auto-rotate'?: boolean;
  'auto-rotate-delay'?: string | number;
  'rotation-per-second'?: string;
  'interaction-prompt'?: string;
  'interaction-prompt-threshold'?: string | number;
  'interaction-prompt-style'?: string;

  // Lighting and environment
  'environment-image'?: string;
  'skybox-image'?: string;
  exposure?: string | number;
  'shadow-intensity'?: string | number;
  'shadow-softness'?: string | number;

  // Animation
  'animation-name'?: string;
  'animation-crossfade-duration'?: string | number;
  autoplay?: boolean;

  // Loading
  loading?: 'auto' | 'lazy' | 'eager';
  reveal?: 'auto' | 'interaction' | 'manual';

  // Annotations
  'disable-zoom'?: boolean;

  // Staging
  'stage-light-intensity'?: string | number;

  // Events (React style)
  onLoad?: (event: Event) => void;
  onError?: (event: ErrorEvent) => void;
  onProgress?: (event: ProgressEvent) => void;
  onModelVisibility?: (event: CustomEvent) => void;
  onCameraChange?: (event: CustomEvent) => void;

  // Style (inline styles)
  style?: React.CSSProperties;

  // Standard HTML attributes
  className?: string;
  id?: string;

  // Slots for custom content
  children?: React.ReactNode;
}

// For importing the web component script
declare module '@google/model-viewer' {
  export default class ModelViewer extends HTMLElement {
    src: string;
    poster: string;
    alt: string;
    ar: boolean;
    autoplay: boolean;
    cameraControls: boolean;
    environmentImage: string;
    exposure: number;
    shadowIntensity: number;

    // Methods
    play(): void;
    pause(): void;
    resetTurntableRotation(): void;

    // Events
    addEventListener(type: 'load', listener: (event: Event) => void): void;
    addEventListener(type: 'error', listener: (event: ErrorEvent) => void): void;
    addEventListener(type: 'progress', listener: (event: ProgressEvent) => void): void;
  }
}

export { };