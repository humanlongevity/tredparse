import React from 'react';
import { Meteor } from 'meteor/meteor';
import { Grid } from 'react-bootstrap';

const App = ({ children }) => (
  <div>
    <Grid>
      { children }
    </Grid>
  </div>
);

App.propTypes = {
  children: React.PropTypes.node,
};

export default App;
