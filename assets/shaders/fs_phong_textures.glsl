#version 300 es
precision mediump float;

in vec3 v_normal;
in vec3 v_surfaceWorldPosition;
in vec2 v_texcoord;

uniform vec3 u_viewWorldPosition;
uniform vec3 u_lightWorldPosition;
uniform vec3 u_ambientColor;
uniform vec3 u_diffuseColor;
uniform vec3 u_specularColor;
uniform float u_shininess;
uniform sampler2D u_texture;

out vec4 outColor;

void main() {
  vec3 normal = normalize(v_normal);
  vec3 surfaceToLightDirection = normalize(u_lightWorldPosition - v_surfaceWorldPosition);
  vec3 surfaceToViewDirection = normalize(u_viewWorldPosition - v_surfaceWorldPosition);
  vec3 halfVector = normalize(surfaceToLightDirection + surfaceToViewDirection);

  // Obtener el color base desde la textura
  vec4 texColor = texture(u_texture, v_texcoord);

  // Cálculo de luz difusa (Lambert)
  float light = max(dot(normal, surfaceToLightDirection), 0.0);
  
  // Cálculo de luz especular (Blinn-Phong)
  float specular = 0.0;
  if (light > 0.0) {
    specular = pow(max(dot(normal, halfVector), 0.0), u_shininess);
  }

  // Combinar ambiente + difusa + especular
  vec3 finalColor = u_ambientColor * texColor.rgb +
                    texColor.rgb * light +
                    u_specularColor * specular;

  outColor = vec4(finalColor, texColor.a);
}