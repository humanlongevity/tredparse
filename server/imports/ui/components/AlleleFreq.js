import React from 'react';
import d3 from 'd3';
import { Treds } from './TredTable';

const getData = (text) => {
  const data = text.replace(/{|}/g, '')
                    .split(',')
                    .map(d => d.split(':')
                    .map(d => +d));
  return data;
};

const update = (props) => {
  const tred = Treds[props.tred];
  const data = getData(tred.allele_freq);
  const choose = choices => choices[Math.floor(Math.random() * choices.length)];
  const color = choose(d3.schemeCategory20);

  return (me) => {
    me.select('svg').remove();
    const canvas = { width: 360, height: 280 };
    const svg = me.append('svg')
                  .attr('width', canvas.width)
                  .attr('height', canvas.height);
    const margin = { top: 10, right: 30, bottom: 30, left: 50 };
    const width = +svg.attr('width') - margin.left - margin.right;
    const height = +svg.attr('height') - margin.top - margin.bottom;
    const g = svg.append('g')
              .attr('transform', `translate(${margin.left}, ${margin.top})`);

    const cutoffRisk = +tred.cutoff_risk;
    const maxSize = Math.max(d3.max(data, d => d[0]), cutoffRisk);
    const x = d3.scaleLinear()
                .domain([0, maxSize])
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
        .attr('width', x(0.9))
        .attr('height', d => height - y(d[1]));
    g.append('g')
      .attr('transform', `translate(0, ${height})`)
      .call(d3.axisBottom(x));
    g.append('g')
      .call(d3.axisLeft(y));

    const xlabel = svg.append('text')
                      .attr('text-anchor', 'middle')
                      .attr('transform', `translate(${margin.left + width / 2}, ${+svg.attr('height')})`)
                      .text(`Number of ${tred.repeat}s at ${props.tred} locus`);

    // Cutoff line
    const linePos = x(cutoffRisk) + margin.left;
    const line = svg.append('line')
                    .attr('x1', linePos)
                    .attr('y1', margin.top)
                    .attr('x2', linePos)
                    .attr('y2', margin.top + height)
                    .style('stroke-width', 3)
                    .style('stroke', 'tomato')
                    .style('fill', 'none');

    let patients = 0;
    const expansion = (tred.mutation_nature === 'increase');
    data.forEach(d => {
      if (expansion && d[0] >= cutoffRisk) {
        patients += d[1];
      } else if (!expansion && d[0] <= cutoffRisk) {
        patients += d[1];
      }
    });

    // Comment on the line
    const pad = expansion ? 15 : -5;
    const tag = expansion ? '\u2265': '\u2264';
    const comment = svg.append('text')
                       .attr('text-anchor', 'middle')
                       .attr('transform', `translate(${linePos + pad}, ${margin.top + height / 2}) rotate(-90)`)
                       .text(`Disease (${tag}${cutoffRisk} ${tred.repeat}s) - ${patients} alleles`);
  };
};

const AlleleFreq = React.createClass({
  propTypes: {
    tred: React.PropTypes.string,
  },

  componentDidMount() {
    d3.select(this.refs.alleleFreq)
      .call(update(this.props));
  },

  shouldComponentUpdate(props) {
    d3.select(this.refs.alleleFreq)
      .call(update(props));

    // Always skip React's render step
    return false;
  },

  render() {
    return (
      <div ref='alleleFreq'></div>
    );
  },
});

module.exports = AlleleFreq;
