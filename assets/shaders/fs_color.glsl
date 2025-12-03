#version 300 es
precision highp float;

// in vec4 v_color;
uniform vec4 ucolor;
uniform float u_lightIntensity;

out vec4 outColor;

void main() {
    outColor = vec4(ucolor.rgb * u_lightIntensity, ucolor.a);
}
