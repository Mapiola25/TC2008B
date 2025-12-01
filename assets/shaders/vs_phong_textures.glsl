#version 300 es
in vec4 a_position;
in vec3 a_normal;
in vec2 a_texcoord;

uniform mat4 u_transforms; // Matriz World-View-Projection
uniform mat4 u_world;      // Matriz Mundo (Model)

out vec3 v_normal;
out vec3 v_surfaceWorldPosition;
out vec2 v_texcoord;

void main() {
  // Posición final en pantalla
  gl_Position = u_transforms * a_position;

  // Calcular posición en el mundo para la iluminación
  v_surfaceWorldPosition = (u_world * a_position).xyz;

  // Orientar normales según la rotación del objeto
  v_normal = mat3(u_world) * a_normal;

  // Pasar coordenadas de textura al fragment shader
  v_texcoord = a_texcoord;
}