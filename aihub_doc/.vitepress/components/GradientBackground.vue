<template>
  <div class="sidebar-gradient-bg">
    <!-- SVG filter for goo effect -->
    <svg class="hidden">
      <defs>
        <filter id="goo">
          <feGaussianBlur
            in="SourceGraphic"
            stdDeviation="10"
            result="blur"
          />
          <feColorMatrix
            in="blur"
            mode="matrix"
            values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 19 -9"
            result="goo"
          />
          <feComposite
            in="SourceGraphic"
            in2="goo"
            operator="atop"
          />
        </filter>
      </defs>
    </svg>

    <div class="gradients-container absolute inset-0">
      <div class="gradient-orb g1" />
      <div class="gradient-orb g2" />
      <div class="gradient-orb g3" />
      <div class="gradient-orb g4" />
      <div class="gradient-orb g5" />
    </div>

    <div class="fadeout-gradient"></div>
  </div>
</template>
<style>
.gradients-container {
  filter: url(#goo) blur(120px);
}

.sidebar-gradient-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: transparent;
  overflow: hidden;
}

.fadeout-gradient {
  position: absolute;
  height: 150px;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(to bottom, rgba(0, 0, 0, 0) 0%, var(--vp-c-bg) 100%);
}

.gradient-orb {
  position: absolute;
  width: 1100px;
  height: 1100px;
  mix-blend-mode: hard-light;
}

/* Gradient 1 - Vertical movement */
.g1 {
  opacity: 0.7;
  background: radial-gradient(circle at center, var(--orb-color) 0%, transparent 50%);
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation: moveVertical 20s ease infinite;
}

/* Gradient 2 - Circular movement (reverse) */
.g2 {
  opacity: 0.7;
  background: radial-gradient(circle at center, var(--orb-color) 0%, transparent 50%);
  top: 10%;
  left: 15%;
  animation: moveInCircle 15s reverse infinite;
  transform: translate(-20%, -20%);
}

/* Gradient 3 - Circular movement */
.g3 {
  opacity: 0.7;
  background: radial-gradient(circle at center, var(--orb-color) 0%, transparent 50%);
  top: 80%;
  left: 80%;
  transform: translate(-50%, -50%);
  animation: moveInCircle 25s linear infinite;
}

/* Gradient 4 - Horizontal movement */
.g4 {
  opacity: 0.7;
  background: radial-gradient(circle at center, var(--orb-color) 0%, transparent 50%);
  top: 50%;
  left: 30%;
  transform: translate(-50%, -50%);
  animation: moveHorizontal 30s ease infinite;
}

/* Gradient 5 - Diagonal movement */
.g5 {
  opacity: 0.7;
  background: radial-gradient(circle at center, var(--orb-color) 0%, transparent 50%);
  top: 70%;
  left: 60%;
  transform: translate(-50%, -50%);
  animation: moveDiagonal 18s ease infinite;
}

/* Animations */
@keyframes moveVertical {
  0%, 100% {
    transform: translate(-50%, -50%) translateY(-150px);
  }
  50% {
    transform: translate(-50%, -50%) translateY(1050px);
  }
}

@keyframes moveInCircle {
  from {
    transform: translate(-30%, -30%) rotate(0deg) translateY(360px) rotate(0deg);
  }
  to {
    transform: translate(-30%, -30%) rotate(360deg) translateY(360px) rotate(-360deg);
  }
}

@keyframes moveHorizontal {
  0%, 100% {
    transform: translate(-50%, -50%) translateX(-350px);
  }
  50% {
    transform: translate(-50%, -50%) translateX(350px);
  }
}

@keyframes moveDiagonal {
  0%, 100% {
    transform: translate(-50%, -50%) translate(-30px, 230px);
  }
  50% {
    transform: translate(-50%, -50%) translate(150px, 1030px);
  }
}
</style>