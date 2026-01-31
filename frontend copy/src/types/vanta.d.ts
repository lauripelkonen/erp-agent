declare module 'vanta/dist/vanta.dots.min.js' {
  interface VantaDotsOptions {
    el: HTMLElement;
    THREE: any;
    mouseControls?: boolean;
    touchControls?: boolean;
    gyroControls?: boolean;
    minHeight?: number;
    minWidth?: number;
    scale?: number;
    scaleMobile?: number;
    color?: number;
    color2?: number;
    backgroundColor?: number;
    size?: number;
    spacing?: number;
    showLines?: boolean;
  }

  interface VantaEffect {
    destroy(): void;
  }

  function DOTS(options: VantaDotsOptions): VantaEffect;
  export default DOTS;
}
