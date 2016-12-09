import React from 'react';

const TredparseResults = React.createClass({
  propTypes: {
    content: React.PropTypes.string,
  },

  render() {
    return (
      <div>
        { this.props.content }
      </div>
    );
  },
});

export default TredparseResults;
