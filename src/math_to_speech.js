const SRE = require('speech-rule-engine');
const temml = require('temml');
const readline = require('readline');

(async () => {
  await SRE.setupEngine({ locale: 'en', domain: 'clearspeak', style: 'default' });

  const rl = readline.createInterface({ input: process.stdin });

  let input = '';
  rl.on('line', line => input += line);
  rl.on('close', () => {
    try {
      const mathml = temml.renderToString(input.trim(), { displayMode: false });
      const speech = SRE.toSpeech(mathml);
      console.log(speech);
    } catch (err) {
      console.error('ERROR:', err.message);
      process.exit(1);
    }
  });
})();

// // math_to_speech.js
// const SRE = require('speech-rule-engine');
// const temml = require('temml');
// const readline = require('readline');

// (async () => {
//   await SRE.setupEngine({ locale: 'en', domain: 'mathspeak', style: 'default' });

//   const rl = readline.createInterface({ input: process.stdin });

//   let input = '';
//   rl.on('line', line => input += line);
//   rl.on('close', () => {
//     try {
//       const mathml = temml.renderToString(input.trim(), { displayMode: false });
//       const speech = SRE.toSpeech(mathml);
//       console.log(speech);
//     } catch (err) {
//       console.error('ERROR:', err.message);
//       process.exit(1);
//     }
//   });
// })();
