import { Mongo } from 'meteor/mongo';
import { SimpleSchema } from 'meteor/aldeed:simple-schema';
import { Factory } from 'meteor/dburles:factory';

const Documents = new Mongo.Collection('Documents');
export default Documents;

Documents.allow({
  insert: () => false,
  update: () => false,
  remove: () => false,
});

Documents.deny({
  insert: () => true,
  update: () => true,
  remove: () => true,
});

Documents.schema = new SimpleSchema({
  title: {
    type: String,
    label: 'The title of the document.',
  },
  body: {
    type: String,
    label: 'The body of the document.',
  },
  stderr: {
    type: String,
    label: 'The stderr for error capture.',
  },
  createdAt: {
    type: Date,
    label: 'The creation time of the document',
  },
});

Documents.attachSchema(Documents.schema);

Factory.define('document', Documents, {
  title: () => 'Factory Title',
  body: () => 'Factory Body',
});
