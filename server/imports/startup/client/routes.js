/* eslint-disable max-len */

import React from 'react';
import { render } from 'react-dom';
import { Router, Route, IndexRoute, browserHistory } from 'react-router';
import { Meteor } from 'meteor/meteor';
import App from '../../ui/layouts/App.js';
import Index from '../../ui/pages/Index.js';

Meteor.startup(() => {
  render(
    <Router history={ browserHistory }>
      <Route path="/" component={ App }>
        <IndexRoute name="index" component={ Index } />
      </Route>
      <Route path="/tred" component={ App }>
        <IndexRoute name="index" component={ Index } />
      </Route>
    </Router>,
    document.getElementById('react-root')
  );
});
