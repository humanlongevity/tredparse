import { Meteor } from 'meteor/meteor';
import { check } from 'meteor/check';
import Documents from '../documents';

Meteor.publish('documents.list', () => Documents.find());

Meteor.publish('documents.viewid', (_id) => {
  check(_id, String);
  return Documents.find(_id);
});

Meteor.publish('documents.viewtitle', (title) => {
  check(title, String);
  return Documents.find({ title });
});