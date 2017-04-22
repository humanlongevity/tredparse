import { SimpleSchema } from 'meteor/aldeed:simple-schema';
import { ValidatedMethod } from 'meteor/mdg:validated-method';
import Documents from './documents';
import rateLimit from '../../modules/rate-limit';

const exec = require('child_process').exec;
const Fiber = require('fibers');

const sanitize = (s) => {
  return s.replace(/[\s,;]/gi, '');
};

const getCmd = (bam, tred, ref) => {
  const b = sanitize(bam);
  const t = sanitize(tred);
  const r = sanitize(ref);
  return `tred.py ${b} --tred ${t} --ref ${r}`;
};

export const upsertDocument = new ValidatedMethod({
  name: 'documents.upsert',

  validate: new SimpleSchema({
    _id: { type: String, optional: true },
    title: { type: String, optional: true },
    body: { type: String, optional: true },
    stderr: { type: String, optional: true },
  }).validator(),

  run(document) {
    return Documents.upsert({ _id: document._id }, { $set: document });
  },
});

export const removeDocument = new ValidatedMethod({
  name: 'documents.remove',

  validate: new SimpleSchema({
    _id: { type: String },
  }).validator(),

  run({ _id }) {
    Documents.remove(_id);
  },
});

export const HLIDocker = new ValidatedMethod({
  name: 'docker.hli',

  validate: new SimpleSchema({
    _id: { type: String, optional: true },
    bam: { type: String, optional: true },
    tred: { type: String, optional: true },
    ref: { type: String, optional: true },
  }).validator(),

  run(document) {

    const title = getCmd(document.bam, document.tred, document.ref);
    // If command already run, then skip
    if (Documents.find({ title }).count()) {
      return null;
    }

    // maxBuffer increased to 1Mb to avoid maxBuffer exceeded error
    const cmd = `docker run --rm tanghaibao/tredparse ${title}`;
    exec(cmd, { maxBuffer: 1024 * 1000 }, (err, stdout, stderr) => {
      if (err) {
          console.error(`exec error: ${err}`);
      }

      const stdoutText = stdout.toString() ? stdout.toString()
                                           : JSON.stringify({ error: err.toString() });
      const stderrText = stderr.toString();

      const output = {
        title,
        body: stdoutText,
        stderr: stderrText,
        createdAt: new Date(),
      };

      Fiber(() => {
        Documents.upsert({ _id: output._id }, { $set: output });
      }).run();
    });
  },
});

export const PublicDocker = new ValidatedMethod({
  name: 'docker.public',

  validate: new SimpleSchema({
    _id: { type: String, optional: true },
    bam: { type: String, optional: true },
    tred: { type: String, optional: true },
    ref: { type: String, optional: true },
  }).validator(),

  run(document) {

    const title = getCmd(document.bam, document.tred, document.ref);
    // If command already run, then skip
    if (Documents.find({ title }).count()) {
      return null;
    }

    // maxBuffer increased to 1Mb to avoid maxBuffer exceeded error
    const cmd = `docker run --rm tanghaibao/tredparse-public ${title}`;
    exec(cmd, { maxBuffer: 1024 * 1000 }, (err, stdout, stderr) => {
      if (err) {
          console.error(`exec error: ${err}`);
      }

      const stdoutText = stdout.toString() ? stdout.toString()
                                           : JSON.stringify({ error: 'TREDPARSE command failed!' });
      const stderrText = stderr.toString();

      const output = {
        title,
        body: stdoutText,
        stderr: stderrText,
        createdAt: new Date(),
      };

      Fiber(() => {
        Documents.upsert({ _id: output._id }, { $set: output });
      }).run();
    });
  },
});

rateLimit({
  methods: [
    upsertDocument,
    removeDocument,
  ],
  limit: 5,
  timeRange: 1000,
});
