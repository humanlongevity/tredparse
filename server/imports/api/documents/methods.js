import { SimpleSchema } from 'meteor/aldeed:simple-schema';
import { ValidatedMethod } from 'meteor/mdg:validated-method';
import Documents from './documents';
import rateLimit from '../../modules/rate-limit';

const spawn = require('child_process').spawn;

export const upsertDocument = new ValidatedMethod({
  name: 'documents.upsert',
  validate: new SimpleSchema({
    _id: { type: String, optional: true },
    title: { type: String, optional: true },
    body: { type: String, optional: true },
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

export const Shell = new ValidatedMethod({
  name: 'shell',
  validate: new SimpleSchema({
    _id: { type: String, optional: true },
    cmd: { type: String, optional: true },
  }).validator(),
  run(document) {
    const child = spawn(document.cmd);
    let output;
    child.stdout.on('data', (data) => {
      console.log(`stdout: ${data}`);
      output = {
        _id: document._id,
        title: document.cmd,
        body: data,
      };
    });

    child.on('close', (code) => {
      console.log(`child process exited with code ${code}`);
      return output;
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
