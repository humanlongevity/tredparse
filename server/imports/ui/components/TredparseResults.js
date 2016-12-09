import React from 'react';

const TredparseResults = React.createClass({
  propTypes: {
    content: React.PropTypes.string,
  },

  render() {
    const content = this.props.content;
    const object = JSON.parse(content);
    const [name, bam, details] = object;
    return (
      <div>
        { JSON.stringify(details) }
      </div>
    );
  },
});

export default TredparseResults;
