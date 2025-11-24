#version 300 es
precision highp float;

// in vec4 v_color;
uniform vec4 ucolor;

out vec4 outColor;

void main() {
    outColor = ucolor;
}
