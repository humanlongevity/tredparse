import React from 'react';
import d3 from 'd3';

const update = (props) => {
  if (!props.data) return;

  const choose = choices => choices[Math.floor(Math.random() * choices.length)];
  const color = choose(d3.schemeCategory20);
  const xmax = 100;

  return (me) => {
    me.select('svg').remove();

    let data = [];
    for (let i = 0; i <= xmax; i++) {
        data.push([i, props.data['' + i] || 0]);
    }

    const canvas = { width: 360, height: 200 };
    const svg = me.append('svg')
                  .attr('width', canvas.width)
                  .attr('height', canvas.height);
    const margin = { top: 10, right: 30, bottom: 50, left: 50 };
    const width = +svg.attr('width') - margin.left - margin.right;
    const height = +svg.attr('height') - margin.top - margin.bottom;
    const g = svg.append('g')
              .attr('transform', `translate(${margin.left}, ${margin.top})`);

    const x = d3.scaleLinear()
                .domain([0, xmax])
                .range([0, width]);
    const y = d3.scaleLinear()
                .domain([0, d3.max(data, d => d[1])])
                .range([height, 0]);

    // define the line
    const valueline = d3.line()
        .x(d => x(d[0]))
        .y(d => y(d[1]));

    // add the valueline path.
    g.append('path')
        .data([data])
        .attr('class', 'line')
        .attr('d', valueline)
        .style('stroke-width', 3)
        .style('stroke', color)
        .style('fill', 'none');

    g.append('g')
      .attr('transform', `translate(0, ${height})`)
      .call(d3.axisBottom(x));
    g.append('g')
      .call(d3.axisLeft(y));

    const xlabel = svg.append('text')
                      .attr('text-anchor', 'middle')
                      .attr('transform', `translate(${margin.left + width / 2}, ${svg.attr('height') - 20})`)
                      .text(`${props.label}`);
  };
};

const ProbDist = React.createClass({
  propTypes: {
    data: React.PropTypes.object,
    label: React.PropTypes.string,
  },

  componentDidMount() {
    if (this.props.data) {
      d3.select(this.refs.probDist)
      .call(update(this.props));
    }
  },

  shouldComponentUpdate(props) {
    try {
      d3.select(this.refs.probDist)
      .call(update(props));
    }
    finally {
      // Always skip React's render step
      return false;
    }
  },

  render() {
    return (
      <div ref='probDist'></div>
    );
  },
});

module.exports = ProbDist;
