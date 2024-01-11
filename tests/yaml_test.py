# import yaml
# from datetime import timedelta

# def value( **kwargs ):
#     print( kwargs )
#     return 10


# def value_constructor( loader: yaml.SafeLoader, node: yaml.nodes.MappingNode ) -> int:
#     return timedelta( **loader.construct_mapping( node ) )

# loader = yaml.SafeLoader
# loader.add_constructor( "!value", value_constructor )

# with open( 'test.yaml' ) as file:
#     data = yaml.load( file, Loader=loader )


# print( data )

import re

str = "data(other_data)"
match = re.findall( '[(](.*?)[)]', str )

print( match )