import yaml
from yamlinclude import YamlIncludeConstructor
from config.models.random import WLDRandInt
from config.models.list import WLDRandList
from config.handler import CONFIG_DIR

## Define our own constructors for yaml here.
class WLDYaml():
    ## define our loader so we can over-ride __init__ to automatically add our constructors etc.
    class WLDYamlLoader( yaml.SafeLoader ):
        def __init__(self, stream ) -> None:
            super().__init__(stream)

            ## add constructors
            self.add_constructor( "!rand_list", WLDYaml._rand_list_constructor )
            self.add_constructor( "!rand_int", WLDYaml._rand_int_constructor )
            
            YamlIncludeConstructor.add_to_loader_class( WLDYaml.WLDYamlLoader, base_dir=CONFIG_DIR )
        
    ## define constructors:    
    @staticmethod
    def _rand_list_constructor( loader: WLDYamlLoader, node: yaml.nodes.ScalarNode ) -> WLDRandList:
        return WLDRandList( name=node.value )
    
    @staticmethod
    def _rand_int_constructor( loader: WLDYamlLoader, node: yaml.nodes.Node ) -> WLDRandInt|None:
        if isinstance( node, yaml.nodes.MappingNode ):
            return WLDRandInt( **loader.construct_mapping(node) ) # type: ignore
        elif isinstance( node, yaml.nodes.ScalarNode ):
            value = node.value
            if str(value).isdigit():
                return WLDRandInt( max=int(value) )
            else:
                return WLDRandInt( key=str(value) )
        elif isinstance( node, yaml.nodes.SequenceNode ):
            return WLDRandInt( key=str(node.value[0].value), min=int(node.value[1].value), max=int(node.value[2].value) )
        
        print( f"!rand_int constructor - error parsing node {node.start_mark}" )
    
    ## define our dumper so we can over-ride __init__ to automatically add our constructors etc.
    class WLDYamlDumper( yaml.SafeDumper ):
        def __init__(self, **kwargs ) -> None:
            super().__init__(**kwargs)