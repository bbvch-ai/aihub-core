import upstream from './vite.config';
import { openWebuiModHost } from './aihub-mods/host_plugin.mjs';

export default { ...upstream, plugins: [...openWebuiModHost(), ...upstream.plugins] };
