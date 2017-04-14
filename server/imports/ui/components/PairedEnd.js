import React from 'react';
import d3 from 'd3';
import { getData } from './TredTable';

const update = (props) => {
  const choose = choices => choices[Math.floor(Math.random() * choices.length)];
  const color = choose(d3.schemeCategory20);

  return (me) => {
    me.select('svg').remove();
    const data = getData(props.data);

    const canvas = { width: 360, height: 180 };
    const svg = me.append('svg')
                  .attr('width', canvas.width)
                  .attr('height', canvas.height);
    const margin = { top: 10, right: 30, bottom: 30, left: 50 };
    const width = +svg.attr('width') - margin.left - margin.right;
    const height = +svg.attr('height') - margin.top - margin.bottom;
    const g = svg.append('g')
              .attr('transform', `translate(${margin.left}, ${margin.top})`);

    const x = d3.scaleLinear()
                .domain([0, 1000])
                .range([0, width]);
    const y = d3.scaleLinear()
                .domain([0, d3.max(data, d => d[1])])
                .range([height, 0]);
    const bar = g.selectAll('.bar')
                  .data(data)
                  .enter().append('g')
                  .attr('fill', color);

    bar.append('rect')
        .attr('x', d => x(d[0]))
        .attr('y', d => y(d[1]))
        .attr('width', x(0.9 * 25))
        .attr('height', d => height - y(d[1]));
    g.append('g')
      .attr('transform', `translate(0, ${height})`)
      .call(d3.axisBottom(x));
    g.append('g')
      .call(d3.axisLeft(y));

    const xlabel = svg.append('text')
                      .attr('text-anchor', 'middle')
                      .attr('transform', `translate(${margin.left + width / 2}, ${+svg.attr('height')})`)
                      .text('Paired-end distance (bp)');
  };
};

const PairedEnd = React.createClass({
  propTypes: {
    data: React.PropTypes.string,
  },

  componentDidMount() {
    d3.select(this.refs.pairedEnd)
      .call(update(this.props));
  },

  shouldComponentUpdate(props) {
    d3.select(this.refs.pairedEnd)
      .call(update(props));

    // Always skip React's render step
    return false;
  },

  render() {
    return (
      <div ref='pairedEnd'></div>
    );
  },
});

module.exports = PairedEnd;
